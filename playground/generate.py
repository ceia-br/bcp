import argparse
import base64
import copy
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from a2a import types as a2a_types
from cryptography.hazmat.primitives.asymmetric import ec
from google.protobuf.json_format import ParseDict
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

PLAYGROUND_DIR = Path(__file__).resolve().parent
PROTOCOL_DIR = PLAYGROUND_DIR.parent
SCENARIO_PATH = PLAYGROUND_DIR / "scenario.json"
SNAPSHOTS_DIR = PLAYGROUND_DIR / "snapshots"
STEPS_DIR = SNAPSHOTS_DIR / "steps"

_BCP_EXTENSION_URI = "https://bcp.dev.br/2026-04-08/specification/reference"
_PROFILE_SCHEMA_URI = "https://bcp.dev.br/schemas/discovery/profile.json"
_CATALOG_SEARCH_SCHEMA_URI = "https://bcp.dev.br/schemas/shopping/catalog_search.json"
_CHECKOUT_SCHEMA_URI = "https://bcp.dev.br/schemas/shopping/checkout.json"
_PIX_SCHEMA_URI = "https://bcp.dev.br/schemas/handlers/pix/pix.json"
_ORDER_CONFIRMATION_SCHEMA_URI = "https://bcp.dev.br/schemas/shopping/types/order_confirmation.json"
_ORDER_SCHEMA_URI = "https://bcp.dev.br/schemas/shopping/order.json"
_NFE_SCHEMA_URI = "https://bcp.dev.br/schemas/shopping/nfe.json"
_CHECKOUT_CAPABILITY = "br.dev.bcp.shopping.checkout"
_CHECKOUT_EXTENSIONS = (
    "fiscal_identity",
    "tax",
    "fulfillment",
    "buyer_consent",
)

_P256_N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551

JsonObject = dict[str, Any]


def _load_json(path: Path) -> JsonObject:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object in {path}")
    return value


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _private_key(label: str) -> ec.EllipticCurvePrivateKey:
    scalar = int.from_bytes(hashlib.sha256(label.encode()).digest(), "big")
    return ec.derive_private_key(scalar % (_P256_N - 1) + 1, ec.SECP256R1())


def _public_jwk(key_id: str, private_key: ec.EllipticCurvePrivateKey) -> JsonObject:
    numbers = private_key.public_key().public_numbers()
    return {
        "kid": key_id,
        "kty": "EC",
        "crv": "P-256",
        "x": _base64url(numbers.x.to_bytes(32, "big")),
        "y": _base64url(numbers.y.to_bytes(32, "big")),
        "use": "sig",
        "alg": "ES256",
    }


def _schema_registry() -> Registry[Any]:
    registry: Registry[Any] = Registry()
    paths = sorted((PROTOCOL_DIR / "schemas").rglob("*.json"))
    paths.extend(sorted((PROTOCOL_DIR / "discovery").rglob("*.json")))
    for path in paths:
        schema = _load_json(path)
        schema_id = schema.get("$id")
        if isinstance(schema_id, str):
            resource = Resource.from_contents(schema)
            registry = registry.with_resource(schema_id, resource)
            if schema_id.startswith("https://bcp.dev.br/schemas/"):
                # profile_schema.json has a legacy ../schemas ref; its dependency graph
                # consequently resolves under /schemas/schemas/ during local validation.
                registry = registry.with_resource(
                    schema_id.replace(
                        "https://bcp.dev.br/schemas/",
                        "https://bcp.dev.br/schemas/schemas/",
                        1,
                    ),
                    resource,
                )
    return registry


def _validate_schema(value: Any, schema_uri: str, registry: Registry[Any]) -> None:
    wrapper = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$ref": schema_uri,
    }
    Draft202012Validator(
        wrapper,
        registry=registry,
        format_checker=FormatChecker(),
    ).validate(value)


def _capability_definitions(version: str, *, full: bool, advertise_all: bool = False) -> JsonObject:
    versions = {
        "checkout": version,
        "fiscal_identity": "2026-07-03",
        "tax": "2026-07-14",
        "fulfillment": version,
        "buyer_consent": version,
    }
    if advertise_all:
        versions.update(
            {
                "catalog.search": version,
                "order": version,
                "nfe": version,
            }
        )
    capabilities: JsonObject = {}
    for name, capability_version in versions.items():
        capability_name = f"br.dev.bcp.shopping.{name}"
        entry: JsonObject = {"version": capability_version}
        if name == "nfe":
            entry["extends"] = "br.dev.bcp.shopping.order"
        elif name not in {"checkout", "catalog.search", "order"}:
            entry["extends"] = _CHECKOUT_CAPABILITY
        if full:
            schema_name = "catalog_search" if name == "catalog.search" else name
            spec_name = "catalog/search" if name == "catalog.search" else name.replace("_", "-")
            entry.update(
                {
                    "spec": f"https://bcp.dev.br/{version}/specification/{spec_name}",
                    "schema": f"https://bcp.dev.br/schemas/shopping/{schema_name}.json",
                }
            )
        capabilities[capability_name] = [entry]
    return capabilities


def _payment_handler(scenario: Mapping[str, Any], *, profile: bool) -> JsonObject:
    fixed = scenario["fixed"]
    entry: JsonObject = {
        "id": fixed["payment_handler_id"],
        "version": "2026-07-08",
        "available_instruments": [{"type": "pix"}],
        "config": {"environment": "sandbox"},
    }
    if profile:
        entry.update(
            {
                "spec": "https://bcp.dev.br/2026-07-08/specification/pix-payment-handler",
                "schema": _PIX_SCHEMA_URI,
            }
        )
    else:
        entry["config"]["payee_name"] = scenario["seller"]["display_name"]
    return {"br.dev.bcp.pix": [entry]}


def _seller_profile(
    scenario: Mapping[str, Any], merchant_key: ec.EllipticCurvePrivateKey
) -> JsonObject:
    version = scenario["versions"]["bcp"]
    seller_agent = scenario["participants"]["seller_agent"]
    return {
        "ucp": {
            "version": version,
            "services": {
                "br.dev.bcp.shopping": [
                    {
                        "version": version,
                        "spec": f"https://bcp.dev.br/{version}/specification/overview",
                        "transport": "a2a",
                        "endpoint": seller_agent["agent_card_url"],
                    }
                ]
            },
            "capabilities": _capability_definitions(version, full=True, advertise_all=True),
            "payment_handlers": _payment_handler(scenario, profile=True),
        },
        "keys": [_public_jwk(seller_agent["key_id"], merchant_key)],
    }


def _agent_card(scenario: Mapping[str, Any]) -> JsonObject:
    version = scenario["versions"]["a2a"]
    seller_agent = scenario["participants"]["seller_agent"]
    capabilities = _capability_definitions(
        scenario["versions"]["bcp"], full=False, advertise_all=True
    )
    return {
        "name": scenario["seller"]["display_name"],
        "description": "Agente vendedor determinístico do playground BCP",
        "supportedInterfaces": [
            {
                "url": seller_agent["a2a_url"],
                "protocolBinding": "JSONRPC",
                "protocolVersion": version,
            }
        ],
        "provider": {
            "organization": scenario["seller"]["legal_name"],
            "url": "https://loja.exemplo",
        },
        "version": "1.0.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "extensions": [
                {
                    "uri": _BCP_EXTENSION_URI,
                    "description": "BCP checkout binding",
                    "required": True,
                    "params": {"capabilities": capabilities},
                }
            ],
        },
        "defaultInputModes": ["text/plain", "application/json"],
        "defaultOutputModes": ["text/plain", "application/json"],
        "skills": [
            {
                "id": "bcp-checkout",
                "name": "BCP checkout",
                "description": "Busca em prosa e checkout BCP determinístico",
                "tags": ["commerce", "checkout", "pix"],
                "inputModes": ["text/plain", "application/json"],
                "outputModes": ["text/plain", "application/json"],
            }
        ],
    }


def _response_ucp(scenario: Mapping[str, Any]) -> JsonObject:
    version = scenario["versions"]["bcp"]
    return {
        "version": version,
        "capabilities": _capability_definitions(version, full=False),
        "payment_handlers": _payment_handler(scenario, profile=False),
    }


def _base_checkout(scenario: Mapping[str, Any]) -> JsonObject:
    fixed = scenario["fixed"]
    product = scenario["product"]
    tax_amount = sum(item["amount"] for item in product["taxes"])
    return {
        "ucp": _response_ucp(scenario),
        "id": fixed["checkout_id"],
        "status": "incomplete",
        "currency": "BRL",
        "seller_identity": {
            "cnpj": scenario["seller"]["cnpj"],
            "legal_name": scenario["seller"]["legal_name"],
        },
        "line_items": [
            {
                "id": fixed["line_item_id"],
                "item": {
                    "id": product["id"],
                    "title": product["title"],
                    "price": product["price"],
                },
                "quantity": 1,
                "ncm": product["ncm"],
                "taxes": copy.deepcopy(product["taxes"]),
                "totals": [{"type": "subtotal", "amount": product["price"]}],
            }
        ],
        "totals": [
            {"type": "subtotal", "amount": product["price"]},
            {
                "type": "tax",
                "display_text": "Tributos aproximados incluídos no preço",
                "amount": tax_amount,
            },
            {"type": "total", "amount": product["price"]},
        ],
        "messages": [
            {
                "type": "info",
                "path": "$.buyer",
                "content": "Informe comprador, CPF, destino, frete e consentimentos.",
            }
        ],
        "links": [
            {"type": "privacy_policy", "url": scenario["seller"]["privacy_url"]},
            {"type": "terms_of_service", "url": scenario["seller"]["terms_url"]},
        ],
        "expires_at": fixed["checkout_expires_at"],
    }


def _delivery_checkout(scenario: Mapping[str, Any], incomplete: JsonObject) -> JsonObject:
    checkout = copy.deepcopy(incomplete)
    fixed = scenario["fixed"]
    buyer = scenario["buyer"]
    shipping_options = scenario["shipping"]["options"]
    checkout["buyer"] = {
        "first_name": buyer["first_name"],
        "last_name": buyer["last_name"],
        "email": buyer["email"],
        "phone_number": buyer["phone_number"],
        "taxpayer_id": copy.deepcopy(buyer["taxpayer_id"]),
        "consent": copy.deepcopy(buyer["consent"]),
    }
    checkout["context"] = copy.deepcopy(buyer["context"])
    checkout["fulfillment"] = {
        "methods": [
            {
                "id": fixed["shipping_method_id"],
                "type": "shipping",
                "line_item_ids": [fixed["line_item_id"]],
                "destinations": [
                    {"id": fixed["destination_id"], **copy.deepcopy(buyer["address"])}
                ],
                "selected_destination_id": fixed["destination_id"],
                "groups": [
                    {
                        "id": fixed["shipping_group_id"],
                        "line_item_ids": [fixed["line_item_id"]],
                        "options": [
                            {
                                "id": option["id"],
                                "title": option["title"],
                                "description": option["description"],
                                "carrier": option["carrier"],
                                "earliest_fulfillment_time": option["earliest_fulfillment_time"],
                                "latest_fulfillment_time": option["latest_fulfillment_time"],
                                "totals": [
                                    {
                                        "type": "shipping",
                                        "display_text": option["title"],
                                        "amount": option["price"],
                                    }
                                ],
                            }
                            for option in shipping_options
                        ],
                    }
                ],
            }
        ]
    }
    checkout["messages"] = [
        {
            "type": "info",
            "path": "$.fulfillment.methods[0].groups[0].selected_option_id",
            "content": "Escolha uma opção de frete.",
        }
    ]
    return checkout


def _ready_checkout(scenario: Mapping[str, Any], delivery: JsonObject) -> JsonObject:
    checkout = copy.deepcopy(delivery)
    fixed = scenario["fixed"]
    shipping = next(
        option
        for option in scenario["shipping"]["options"]
        if option["id"] == fixed["shipping_option_id"]
    )
    checkout["status"] = "ready_for_complete"
    checkout.pop("messages", None)
    checkout["fulfillment"]["methods"][0]["groups"][0]["selected_option_id"] = fixed[
        "shipping_option_id"
    ]
    checkout["totals"].insert(
        -1,
        {
            "type": "shipping",
            "display_text": shipping["title"],
            "amount": shipping["price"],
        },
    )
    checkout["totals"][-1]["amount"] = scenario["product"]["price"] + shipping["price"]
    return checkout


def _pix_checkout(scenario: Mapping[str, Any], ready: JsonObject) -> JsonObject:
    checkout = copy.deepcopy(ready)
    fixed = scenario["fixed"]
    total = checkout["totals"][-1]["amount"]
    checkout["payment"] = {
        "instruments": [
            {
                "id": fixed["payment_instrument_id"],
                "handler_id": fixed["payment_handler_id"],
                "type": "pix",
                "selected": True,
                "credential": {
                    "type": "pix_charge",
                    "provider_payment_id": fixed["provider_payment_id"],
                    "copia_e_cola": scenario["pix"]["copia_e_cola"],
                    "payment_url": scenario["pix"]["payment_url"],
                    "expires_at": fixed["pix_expires_at"],
                    "binding": {"checkout_id": fixed["checkout_id"]},
                },
                "display": {
                    "payee_name": scenario["seller"]["display_name"],
                    "description": f"Pague R$ {total / 100:.2f} via Pix. Cobrança demonstrativa.",
                },
            }
        ]
    }
    return checkout


def _completed_checkout(scenario: Mapping[str, Any], checkout: JsonObject) -> JsonObject:
    completed = copy.deepcopy(checkout)
    completed["status"] = "completed"
    completed["order"] = {
        "id": scenario["fixed"]["order_id"],
        "label": f"Pedido {scenario['seller']['display_name']}",
        "permalink_url": scenario["seller"]["order_url"],
    }
    return completed


def _message(
    message_id: str,
    context_id: str | None,
    role: str,
    parts: list[JsonObject],
) -> JsonObject:
    message: JsonObject = {
        "messageId": message_id,
        "role": role,
        "parts": parts,
        "extensions": [_BCP_EXTENSION_URI],
    }
    if context_id is not None:
        message["contextId"] = context_id
    return message


def _rpc_request(
    rpc_id: str,
    message_id: str,
    scenario: Mapping[str, Any],
    parts: list[JsonObject],
    *,
    include_context: bool = True,
) -> JsonObject:
    body = {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "method": "SendMessage",
        "params": {
            "message": _message(
                message_id,
                scenario["fixed"]["context_id"] if include_context else None,
                "ROLE_USER",
                parts,
            )
        },
    }
    return {
        "headers": {
            "BCP-Agent": (f'profile="{scenario["participants"]["buyer_agent"]["profile_url"]}"'),
            "A2A-Extensions": _BCP_EXTENSION_URI,
            "A2A-Version": scenario["versions"]["a2a"],
        },
        "body": body,
    }


def _rpc_response(
    rpc_id: str,
    message_id: str,
    scenario: Mapping[str, Any],
    parts: list[JsonObject],
) -> JsonObject:
    return {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "result": {
            "message": _message(
                message_id,
                scenario["fixed"]["context_id"],
                "ROLE_AGENT",
                parts,
            )
        },
    }


def _text_part(text: str) -> JsonObject:
    return {"text": text}


def _data_part(data: JsonObject) -> JsonObject:
    return {"data": data, "mediaType": "application/json"}


def _protocol(badges: Sequence[str], **values: Any) -> JsonObject:
    result: JsonObject = {"badges": list(badges)}
    result.update({key: value for key, value in values.items() if value is not None})
    return result


def _document(kind: str, name: str, payload: Any) -> JsonObject:
    return {"kind": kind, "name": name, "payload": copy.deepcopy(payload)}


def _dialogue(actor: str, text_pt: str, text_en: str) -> JsonObject:
    return {"actor": actor, "text": {"pt-BR": text_pt, "en": text_en}}


def _event(
    title_pt: str,
    title_en: str,
    description_pt: str,
    description_en: str,
    documents: Sequence[JsonObject],
    conversation: Sequence[JsonObject],
    widget: JsonObject | None = None,
) -> JsonObject:
    event = {
        "title": {"pt-BR": title_pt, "en": title_en},
        "description": {"pt-BR": description_pt, "en": description_en},
        "documents": copy.deepcopy(documents),
        "conversation": copy.deepcopy(conversation),
    }
    if widget is not None:
        event["widget"] = copy.deepcopy(widget)
    return event


def _step_messages(step: Mapping[str, Any], scenario: Mapping[str, Any]) -> list[JsonObject]:
    messages = []
    for message in step["messages"]:
        actor = message["actor"]
        if actor not in {"client", "buyer_agent"}:
            raise ValueError(f"conversation actor is not allowed: {actor}")
        messages.append(
            {
                "actor": actor,
                "actor_label": copy.deepcopy(scenario["participants"][actor]["label"]),
                "text": copy.deepcopy(message["text"]),
            }
        )
    return messages


def _validate_part(part: Mapping[str, Any]) -> None:
    forbidden = {"kind", "type"}.intersection(part)
    if forbidden:
        raise ValueError(f"A2A 1.0 Part contains forbidden discriminator: {sorted(forbidden)}")
    payload_fields = {"text", "raw", "url", "data"}.intersection(part)
    if len(payload_fields) != 1:
        raise ValueError("A2A 1.0 Part must contain exactly one payload field")


def _validate_message(message: Mapping[str, Any]) -> None:
    if message.get("role") not in {"ROLE_USER", "ROLE_AGENT"}:
        raise ValueError("invalid A2A message role")
    parts = message.get("parts")
    if not isinstance(parts, list) or not parts:
        raise ValueError("A2A message must contain parts")
    for part in parts:
        if not isinstance(part, dict):
            raise ValueError("A2A Part must be an object")
        _validate_part(part)


def _validate_a2a_card(card: JsonObject) -> None:
    interfaces = card.get("supportedInterfaces")
    if not isinstance(interfaces, list) or not interfaces:
        raise ValueError("AgentCard must contain supportedInterfaces")
    extensions = card.get("capabilities", {}).get("extensions")
    if not isinstance(extensions, list) or not extensions:
        raise ValueError("AgentCard must declare capabilities.extensions")
    ParseDict(card, a2a_types.AgentCard(), ignore_unknown_fields=False)


def _validate_a2a_rpc(value: JsonObject) -> None:
    body = value.get("body", value)
    if body.get("jsonrpc") != "2.0":
        raise ValueError("A2A JSON-RPC envelope must use jsonrpc 2.0")
    if body.get("method") == "SendMessage":
        params = body.get("params", {})
        message = params.get("message", {})
        _validate_message(message)
        ParseDict(params, a2a_types.SendMessageRequest(), ignore_unknown_fields=False)
        return
    result = body.get("result", {})
    message = result.get("message", {})
    _validate_message(message)
    ParseDict(result, a2a_types.SendMessageResponse(), ignore_unknown_fields=False)


def _validate_checkout(checkout: JsonObject, registry: Registry[Any]) -> None:
    _validate_schema(checkout, _CHECKOUT_SCHEMA_URI, registry)
    for extension in _CHECKOUT_EXTENSIONS:
        uri = f"https://bcp.dev.br/schemas/shopping/{extension}.json#/$defs/{_CHECKOUT_CAPABILITY}"
        _validate_schema(checkout, uri, registry)
    instruments = checkout.get("payment", {}).get("instruments", [])
    for instrument in instruments:
        _validate_schema(instrument, f"{_PIX_SCHEMA_URI}#/$defs/pix_payment_instrument", registry)
    if "order" in checkout:
        _validate_schema(checkout["order"], _ORDER_CONFIRMATION_SCHEMA_URI, registry)
        extra = set(checkout["order"]) - {"id", "label", "permalink_url"}
        if extra:
            raise ValueError(f"OrderConfirmation contains Order-only fields: {sorted(extra)}")


def _catalog_product(product: Mapping[str, Any]) -> JsonObject:
    description = {"plain": product["description"]}
    return {
        "id": product["id"],
        "handle": product["id"],
        "title": product["title"],
        "description": description,
        "url": f"https://loja.exemplo/produtos/{product['id']}",
        "price_range": {
            "min": {"amount": product["price"], "currency": "BRL"},
            "max": {"amount": product["price"], "currency": "BRL"},
        },
        "variants": [
            {
                "id": product["id"],
                "title": product["title"],
                "description": description,
                "price": {"amount": product["price"], "currency": "BRL"},
                "availability": {"available": True, "status": "in_stock"},
            }
        ],
        "tags": ["camiseta", "algodão"],
    }


def _products_widget(products: Sequence[Mapping[str, Any]]) -> JsonObject:
    return {
        "type": "products",
        "items": [
            {
                "id": product["id"],
                "title": product["title"],
                "price": product["price"],
                "color": product["color"],
                "meta": copy.deepcopy(product["meta"]),
                "badge": copy.deepcopy(product["badge"]),
                "best": product["best"],
            }
            for product in products
        ],
    }


def _shipping_widget(scenario: Mapping[str, Any], *, show_selection: bool = False) -> JsonObject:
    selected_id = scenario["fixed"]["shipping_option_id"]
    return {
        "type": "shipping",
        "options": [
            {
                "id": option["id"],
                "title": option["title"],
                "description": option["description"],
                "carrier": option["carrier"],
                "price": option["price"],
                "selected": show_selection and option["id"] == selected_id,
            }
            for option in scenario["shipping"]["options"]
        ],
    }


def _order(scenario: Mapping[str, Any], checkout: Mapping[str, Any]) -> JsonObject:
    version = scenario["versions"]["bcp"]
    product = scenario["product"]
    order = scenario["order"]
    shipping = next(
        option
        for option in scenario["shipping"]["options"]
        if option["id"] == scenario["fixed"]["shipping_option_id"]
    )
    tax_amount = sum(item["amount"] for item in product["taxes"])
    return {
        "ucp": {
            "version": version,
            "capabilities": {
                "br.dev.bcp.shopping.order": [{"version": version}],
                "br.dev.bcp.shopping.nfe": [
                    {
                        "version": version,
                        "extends": "br.dev.bcp.shopping.order",
                    }
                ],
            },
        },
        "id": scenario["fixed"]["order_id"],
        "label": "Pedido Loja Vermelho",
        "checkout_id": scenario["fixed"]["checkout_id"],
        "permalink_url": scenario["seller"]["order_url"],
        "currency": "BRL",
        "line_items": [
            {
                "id": scenario["fixed"]["line_item_id"],
                "item": {
                    "id": product["id"],
                    "title": product["title"],
                    "price": product["price"],
                },
                "quantity": {"original": 1, "total": 1, "fulfilled": 0},
                "totals": [
                    {"type": "subtotal", "amount": product["price"]},
                    {"type": "total", "amount": product["price"]},
                ],
                "status": "processing",
            }
        ],
        "fulfillment": {
            "expectations": [
                {
                    "id": "expectation_playground_001",
                    "line_items": [{"id": scenario["fixed"]["line_item_id"], "quantity": 1}],
                    "method_type": "shipping",
                    "destination": copy.deepcopy(scenario["buyer"]["address"]),
                    "description": shipping["description"],
                    "fulfillable_on": "now",
                }
            ],
            "events": [
                {
                    "id": "fulfillment_event_playground_001",
                    "occurred_at": order["nfe_issued_at"],
                    "type": "processing",
                    "line_items": [{"id": scenario["fixed"]["line_item_id"], "quantity": 1}],
                    "tracking_number": order["tracking"],
                    "tracking_url": order["tracking_url"],
                    "carrier": order["carrier"],
                    "description": f"Envio {order['service']} em preparação.",
                }
            ],
        },
        "totals": [
            {"type": "subtotal", "amount": product["price"]},
            {
                "type": "tax",
                "display_text": "Tributos incluídos no preço",
                "amount": tax_amount,
            },
            {
                "type": "fulfillment",
                "display_text": shipping["title"],
                "amount": shipping["price"],
            },
            {"type": "total", "amount": checkout["totals"][-1]["amount"]},
        ],
        "nfe": {
            "access_key": order["nfe_access_key"],
            "issued_at": order["nfe_issued_at"],
        },
    }


def _order_widget(scenario: Mapping[str, Any]) -> JsonObject:
    order = scenario["order"]
    return {
        "type": "order",
        "id": scenario["fixed"]["order_id"],
        "nfe": order["nfe_number"],
        "carrier": f"{order['carrier']} · {order['service']}",
        "tracking": order["tracking"],
        "eta": copy.deepcopy(order["eta"]),
    }


def _display_events(
    scenario: Mapping[str, Any],
    profile: JsonObject,
    card: JsonObject,
    checkouts: Mapping[str, JsonObject],
    exchanges: Mapping[str, Any],
) -> dict[int, list[JsonObject]]:
    products = scenario["catalog_products"]
    product = scenario["product"]
    tax_amount = sum(item["amount"] for item in product["taxes"])
    tax_amount_pt = f"{tax_amount / 100:.2f}".replace(".", ",")
    selected_shipping = next(
        option
        for option in scenario["shipping"]["options"]
        if option["id"] == scenario["fixed"]["shipping_option_id"]
    )
    total = product["price"] + selected_shipping["price"]
    product_widget = _products_widget(products)
    selected_product_widget = _products_widget(products[:1])
    shipping_widget = _shipping_widget(scenario)
    selected_shipping_widget = _shipping_widget(scenario, show_selection=True)
    pix_widget = {
        "type": "pix",
        "amount": total,
        "code": scenario["pix"]["copia_e_cola"],
    }
    return {
        1: [
            _event(
                "Pedido da cliente",
                "Customer request",
                "A cliente explica o que procura e dá ao agente cliente um motivo para descobrir o vendedor.",
                "The customer explains what she wants, giving the buyer agent a reason to discover the seller.",
                [],
                [
                    _dialogue(
                        "client",
                        "Quero uma camiseta vermelha, tamanho M.",
                        "I want a red T-shirt in size M.",
                    ),
                    _dialogue(
                        "buyer_agent",
                        "Vou verificar se a Loja Vermelho oferece os recursos BCP necessários para atender ao seu pedido.",
                        "I will check whether Red Store offers the BCP capabilities needed to fulfill your request.",
                    ),
                ],
            ),
            _event(
                "Perfil BCP",
                "BCP profile",
                "O agente cliente descobre os serviços e recursos comerciais do vendedor.",
                "The buyer agent discovers the seller's commercial services and capabilities.",
                [
                    _document("request", "/.well-known/bcp", exchanges["discovery"][0]),
                    _document("response", "BCP profile", profile),
                ],
                [
                    _dialogue(
                        "buyer_agent",
                        "Vou descobrir quais recursos BCP este vendedor oferece.",
                        "I will discover which BCP capabilities this seller offers.",
                    )
                ],
            ),
            _event(
                "Agent Card A2A",
                "A2A Agent Card",
                "O agente cliente obtém o Agent Card e confirma como falar com o vendedor.",
                "The buyer agent obtains the Agent Card and confirms how to reach the seller.",
                [
                    _document(
                        "request",
                        "/.well-known/agent-card.json",
                        exchanges["discovery"][1],
                    ),
                    _document("response", "Agent Card", card),
                ],
                [
                    _dialogue(
                        "buyer_agent",
                        "Encontrei seu Agent Card A2A e o endpoint compatível.",
                        "I found your A2A Agent Card and compatible endpoint.",
                    ),
                    _dialogue(
                        "seller_agent",
                        "Estou disponível por A2A 1.0 com a extensão BCP obrigatória.",
                        "I am available over A2A 1.0 with the required BCP extension.",
                    ),
                ],
            ),
            _event(
                "Negociação BCP",
                "BCP negotiation",
                "Os agentes registram as versões e capacidades aceitas para a sessão.",
                "The agents establish the versions and capabilities accepted for the session.",
                [
                    _document("request", "BCP negotiation", exchanges["discovery"][2]),
                    _document(
                        "response",
                        "BCP negotiation",
                        exchanges["discovery_response"]["negotiated"],
                    ),
                ],
                [
                    _dialogue(
                        "buyer_agent",
                        "Proponho esta versão do BCP e estas capacidades comerciais.",
                        "I propose this BCP version and these commercial capabilities.",
                    ),
                    _dialogue(
                        "seller_agent",
                        "Versão e capacidades aceitas para esta sessão.",
                        "Version and capabilities accepted for this session.",
                    ),
                ],
            ),
        ],
        2: [
            _event(
                "Busca no catálogo",
                "Catalog search",
                "O vendedor consulta o catálogo e devolve o match exato seguido das alternativas mais próximas.",
                "The seller searches the catalog and returns the exact match followed by the closest alternatives.",
                [
                    _document("request", "A2A SendMessage", exchanges["catalog_request"]),
                    _document("request", "catalog.search", exchanges["mcp_request"]),
                    _document("response", "catalog.search", exchanges["mcp_response"]),
                    _document("response", "A2A SendMessage", exchanges["catalog_response"]),
                ],
                [
                    _dialogue(
                        "buyer_agent",
                        "Procuro uma camiseta vermelha, tamanho M.",
                        "I am looking for a red T-shirt, size M.",
                    ),
                    _dialogue(
                        "seller_agent",
                        "Vou buscar o match exato e as alternativas mais próximas.",
                        "I will search for the exact match and the closest alternatives.",
                    ),
                    _dialogue(
                        "seller_agent",
                        "Encontrei três opções. A Camiseta Vermelha M é o match exato.",
                        "I found three options. The Red T-shirt M is the exact match.",
                    ),
                ],
                product_widget,
            ),
        ],
        3: [
            _event(
                "Escolha e checkout",
                "Choice and checkout",
                "A cliente confirma o match exato, o agente cliente solicita a inclusão e o vendedor cria o checkout.",
                "The customer confirms the exact match, the buyer agent requests it, and the seller creates the checkout.",
                [
                    _document("request", "add_to_checkout", exchanges["add_request"]),
                    _document("response", "checkout", exchanges["incomplete_response"]),
                ],
                [
                    _dialogue(
                        "buyer_agent",
                        "Encontrei a Camiseta Vermelha M por R$ 59,90. É exatamente a cor e o tamanho que você pediu.",
                        "I found the Red T-shirt M for BRL 59.90. It exactly matches the requested color and size.",
                    ),
                    _dialogue(
                        "client",
                        "Perfeito, quero a vermelha M.",
                        "Perfect, I want the red one in size M.",
                    ),
                    _dialogue(
                        "buyer_agent",
                        f"O vendedor adicionou ao checkout: 1 x Camiseta Vermelha M por R$ 59,90. A nota já sai com os tributos destacados: R$ {tax_amount_pt} de ICMS e PIS/COFINS.",
                        f"The seller added 1 x Red T-shirt M to the checkout for BRL 59.90. The invoice will itemize BRL {tax_amount / 100:.2f} in ICMS and PIS/COFINS taxes.",
                    ),
                ],
                selected_product_widget,
            ),
        ],
        4: [
            _event(
                "Dados de entrega",
                "Delivery details",
                "A cliente confere os dados exatos antes de autorizar o compartilhamento.",
                "The customer reviews the exact details before authorizing their disclosure.",
                [],
                [
                    _dialogue(
                        "buyer_agent",
                        "Tenho Ana Silva, CPF 390.533.447-05, ana@example.com.br, +55 62 99999-0000 e Rua das Flores, 100, Apto 12, Goiânia, GO, CEP 74000-000. Posso usar esses dados e manter os consentimentos opcionais recusados?",
                        "I have Ana Silva, tax ID 390.533.447-05, ana@example.com.br, +55 62 99999-0000, and Rua das Flores, 100, Apt 12, Goiânia, GO, 74000-000. May I use these details and keep optional consents declined?",
                    ),
                    _dialogue(
                        "client",
                        "Sim, os dados estão corretos.",
                        "Yes, the details are correct.",
                    ),
                ],
            ),
            _event(
                "Opções de frete",
                "Shipping options",
                "O vendedor recebe os dados autorizados e devolve todas as opções disponíveis.",
                "The seller receives the authorized details and returns every available option.",
                [
                    _document("request", "A2A SendMessage", exchanges["data_request"]),
                    _document("response", "checkout", exchanges["delivery_response"]),
                ],
                [
                    _dialogue(
                        "buyer_agent",
                        "Envio os dados de entrega autorizados pela cliente.",
                        "I am sending the delivery details authorized by the customer.",
                    ),
                    _dialogue(
                        "seller_agent",
                        "Dados aceitos. Estas são as opções de frete disponíveis.",
                        "Details accepted. These are the available shipping options.",
                    ),
                ],
                shipping_widget,
            ),
        ],
        5: [
            _event(
                "Escolha da entrega",
                "Delivery choice",
                "O agente cliente apresenta as opções recebidas e pede uma escolha explícita.",
                "The buyer agent presents the received options and asks for an explicit choice.",
                [],
                [
                    _dialogue(
                        "buyer_agent",
                        "Há PAC por R$ 19,90 em 4 dias úteis e SEDEX por R$ 34,90 em 2 dias úteis. Qual você prefere?",
                        "PAC costs BRL 19.90 for 4 business days, and SEDEX costs BRL 34.90 for 2 business days. Which do you prefer?",
                    ),
                    _dialogue(
                        "client",
                        "Escolho PAC.",
                        "I choose PAC.",
                    ),
                ],
                selected_shipping_widget,
            ),
            _event(
                "Atualização do frete",
                "Delivery update",
                "O vendedor registra o PAC e recalcula o total do checkout.",
                "The seller records PAC and recalculates the checkout total.",
                [
                    _document("request", "A2A SendMessage", exchanges["shipping_request"]),
                    _document("response", "checkout", exchanges["ready_response"]),
                ],
                [
                    _dialogue(
                        "buyer_agent",
                        "A cliente escolheu PAC por R$ 19,90.",
                        "The customer selected PAC for BRL 19.90.",
                    ),
                    _dialogue(
                        "seller_agent",
                        "PAC selecionado. O total é R$ 79,80 e o checkout está pronto para pagamento.",
                        "PAC selected. The total is BRL 79.80 and the checkout is ready for payment.",
                    ),
                ],
            ),
        ],
        6: [
            _event(
                "Cobrança Pix",
                "Pix charge",
                "O vendedor gera uma cobrança Pix direta para o checkout pronto.",
                "The seller creates a direct Pix charge for the ready checkout.",
                [
                    _document("request", "A2A SendMessage", exchanges["pix_request"]),
                    _document("response", "checkout", exchanges["pix_response"]),
                ],
                [
                    _dialogue(
                        "buyer_agent",
                        "Gere a cobrança Pix para o checkout de R$ 79,80.",
                        "Generate the Pix charge for the BRL 79.80 checkout.",
                    ),
                    _dialogue(
                        "seller_agent",
                        "A cobrança Pix está pronta e aguarda pagamento.",
                        "The Pix charge is ready and awaiting payment.",
                    ),
                ],
            )
        ],
        7: [
            _event(
                "Pagamento via Pix",
                "Pay with Pix",
                "A cliente paga diretamente por Pix. O botão simula a liquidação do mock.",
                "The customer pays directly with Pix. The button simulates mock settlement.",
                [],
                [
                    _dialogue(
                        "buyer_agent",
                        "O Pix de R$ 79,80 está pronto. Escaneie o QR code ou copie o código para pagar.",
                        "The BRL 79.80 Pix charge is ready. Scan the QR code or copy the code to pay.",
                    )
                ],
                pix_widget,
            )
        ],
        8: [
            _event(
                "Pedido confirmado",
                "Order confirmed",
                "Após a liquidação, o checkout é concluído e o agente consulta o pedido completo.",
                "After settlement, the checkout completes and the agent retrieves the full order.",
                [
                    _document("request", "complete_checkout", exchanges["complete_request"]),
                    _document("response", "checkout", exchanges["completed_response"]),
                    _document("request", "GET /orders/{id}", exchanges["order_request"]),
                    _document("response", "order", exchanges["order_response"]),
                ],
                [
                    _dialogue(
                        "buyer_agent",
                        "Pagamento confirmado. Seu pedido foi criado, a NF-e foi autorizada e o rastreio já está disponível.",
                        "Payment confirmed. Your order was created, the invoice was authorized, and tracking is available.",
                    ),
                    _dialogue(
                        "client",
                        "Perfeito, obrigada.",
                        "Perfect, thank you.",
                    ),
                ],
                _order_widget(scenario),
            )
        ],
    }


def _step_protocols(
    scenario: Mapping[str, Any],
    profile: JsonObject,
    card: JsonObject,
    checkouts: Mapping[str, JsonObject],
) -> dict[int, JsonObject]:
    add_request = _rpc_request(
        "rpc-03",
        "msg-03-request",
        scenario,
        [
            _data_part(
                {
                    "action": "add_to_checkout",
                    "product_id": scenario["product"]["id"],
                    "quantity": 1,
                }
            )
        ],
    )
    incomplete_response = _rpc_response(
        "rpc-03",
        "msg-03-response",
        scenario,
        [
            _text_part("Preciso dos dados de entrega, CPF e consentimentos."),
            _data_part({"a2a.bcp.checkout": checkouts["incomplete"]}),
        ],
    )
    data_request = _rpc_request(
        "rpc-04",
        "msg-04-request",
        scenario,
        [
            _text_part(
                "Compradora Ana Silva, CPF 39053344705, ana@example.com.br, "
                "+5562999990000. Entrega na Rua das Flores, 100, Apto 12, "
                "Goiânia, GO, 74000000, BR. Mantenha os consentimentos opcionais "
                "recusados."
            )
        ],
    )
    delivery_response = _rpc_response(
        "rpc-04",
        "msg-04-response",
        scenario,
        [
            _text_part("Dados aceitos. Escolha uma opção de frete."),
            _data_part({"a2a.bcp.checkout": checkouts["delivery"]}),
        ],
    )
    shipping_request = _rpc_request(
        "rpc-05",
        "msg-05-request",
        scenario,
        [_text_part("Escolho PAC por R$ 19,90.")],
    )
    ready_response = _rpc_response(
        "rpc-05",
        "msg-05-response",
        scenario,
        [_data_part({"a2a.bcp.checkout": checkouts["ready"]})],
    )
    pix_request = _rpc_request(
        "rpc-06",
        "msg-06-request",
        scenario,
        [_text_part("Gere a cobrança Pix para o checkout pronto.")],
    )
    pix_response = _rpc_response(
        "rpc-06",
        "msg-06-response",
        scenario,
        [
            _text_part("A cobrança Pix de R$ 79,80 está pronta."),
            _data_part({"a2a.bcp.checkout": checkouts["pix"]}),
        ],
    )
    complete_data = {
        "action": "complete_checkout",
        "a2a.bcp.checkout.payment": copy.deepcopy(checkouts["pix"]["payment"]),
        "a2a.bcp.checkout.signals": copy.deepcopy(scenario["buyer"]["signals"]),
    }
    complete_request = _rpc_request(
        "rpc-07",
        "msg-07-request",
        scenario,
        [_data_part(complete_data)],
    )
    completed_response = _rpc_response(
        "rpc-07",
        "msg-08-response",
        scenario,
        [_data_part({"a2a.bcp.checkout": checkouts["completed"]})],
    )
    catalog_request = _rpc_request(
        "rpc-02",
        "msg-02-request",
        scenario,
        [_text_part("Procuro uma camiseta vermelha, tamanho M.")],
        include_context=False,
    )
    catalog_response = _rpc_response(
        "rpc-02",
        "msg-02-response",
        scenario,
        [_text_part("Encontrei Camiseta Vermelha M, Camiseta Vermelha G e Camiseta Azul M.")],
    )
    catalog_products = [_catalog_product(product) for product in scenario["catalog_products"]]
    mcp_request = {
        "jsonrpc": "2.0",
        "id": "mcp-02",
        "method": "tools/call",
        "params": {
            "name": "search_catalog",
            "arguments": {
                "meta": {
                    "ucp-agent": {"profile": scenario["participants"]["buyer_agent"]["profile_url"]}
                },
                "catalog": {
                    "query": "camiseta vermelha tamanho M",
                    "context": copy.deepcopy(scenario["buyer"]["context"]),
                    "pagination": {"limit": 10},
                },
            },
        },
    }
    mcp_response = {
        "jsonrpc": "2.0",
        "id": "mcp-02",
        "result": {
            "structuredContent": {
                "ucp": {
                    "version": scenario["versions"]["bcp"],
                    "capabilities": {
                        "br.dev.bcp.shopping.catalog.search": [
                            {"version": scenario["versions"]["bcp"]}
                        ]
                    },
                },
                "products": catalog_products,
            }
        },
    }
    discovery_requests = [
        {
            "method": "GET",
            "url": scenario["participants"]["seller_agent"]["profile_url"],
        },
        {
            "method": "GET",
            "url": scenario["participants"]["seller_agent"]["agent_card_url"],
        },
        {
            "headers": {
                "BCP-Agent": (
                    f'profile="{scenario["participants"]["buyer_agent"]["profile_url"]}"'
                ),
                "A2A-Extensions": _BCP_EXTENSION_URI,
                "A2A-Version": scenario["versions"]["a2a"],
            }
        },
    ]
    discovery_response = {
        "business_profile": profile,
        "agent_card": card,
        "negotiated": {"ucp": _response_ucp(scenario)},
    }
    order_response = _order(scenario, checkouts["completed"])
    order_request = {
        "method": "GET",
        "url": f"https://loja.exemplo/orders/{scenario['fixed']['order_id']}",
        "headers": {
            "BCP-Agent": (f'profile="{scenario["participants"]["buyer_agent"]["profile_url"]}"')
        },
    }
    exchanges = {
        "discovery": discovery_requests,
        "discovery_response": discovery_response,
        "catalog_request": catalog_request,
        "catalog_response": catalog_response,
        "mcp_request": mcp_request,
        "mcp_response": mcp_response,
        "add_request": add_request,
        "incomplete_response": incomplete_response,
        "data_request": data_request,
        "delivery_response": delivery_response,
        "shipping_request": shipping_request,
        "ready_response": ready_response,
        "pix_request": pix_request,
        "pix_response": pix_response,
        "complete_request": complete_request,
        "completed_response": completed_response,
        "order_request": order_request,
        "order_response": order_response,
    }
    events = _display_events(scenario, profile, card, checkouts, exchanges)
    return {
        1: _protocol(
            ["BCP discovery", "A2A 1.0 AgentCard", "BCP negotiation"],
            request=discovery_requests,
            response=discovery_response,
            events=events[1],
        ),
        2: _protocol(
            ["A2A TextPart", "MCP search_catalog", "BCP catalog.search"],
            request=catalog_request,
            response=catalog_response,
            internal={
                "title": {
                    "pt-BR": "Consulta interna ao catálogo do vendedor",
                    "en": "Seller-side catalog lookup",
                },
                "description": {
                    "pt-BR": (
                        "Após receber a intenção por A2A, o agente vendedor consulta "
                        "seu catálogo BCP por MCP antes de responder."
                    ),
                    "en": (
                        "After receiving the intent over A2A, the seller agent queries "
                        "its BCP catalog over MCP before replying."
                    ),
                },
                "request": mcp_request,
                "response": mcp_response,
            },
            events=events[2],
        ),
        3: _protocol(
            ["A2A DataPart", "BCP checkout"],
            request=add_request,
            response=incomplete_response,
            checkout=checkouts["incomplete"],
            events=events[3],
        ),
        4: _protocol(
            ["A2A TextPart", "sem action normativa de update"],
            request=data_request,
            response=delivery_response,
            checkout=checkouts["delivery"],
            events=events[4],
        ),
        5: _protocol(
            ["A2A TextPart", "BCP checkout ready_for_complete"],
            request=shipping_request,
            response=ready_response,
            checkout=checkouts["ready"],
            events=events[5],
        ),
        6: _protocol(
            ["A2A", "BCP checkout", "Pix charge"],
            request=pix_request,
            response=pix_response,
            checkout=checkouts["pix"],
            events=events[6],
        ),
        7: _protocol(
            ["Pix direto", "liquidação demonstrativa"],
            checkout=checkouts["pix"],
            events=events[7],
        ),
        8: _protocol(
            ["BCP completed", "OrderConfirmation", "BCP order", "NF-e"],
            request=complete_request,
            response=completed_response,
            checkout=checkouts["completed"],
            order=order_response,
            events=events[8],
        ),
    }


def _build_files(scenario: JsonObject) -> dict[Path, JsonObject]:
    if len(scenario.get("steps", [])) != 8:
        raise ValueError("the playground scenario must define exactly 8 checkpoints")
    registry = _schema_registry()
    merchant_key = _private_key("bcp-playground-merchant-es256")
    profile = _seller_profile(scenario, merchant_key)
    card = _agent_card(scenario)
    _validate_schema(profile, _PROFILE_SCHEMA_URI, registry)
    _validate_a2a_card(card)

    incomplete = _base_checkout(scenario)
    delivery = _delivery_checkout(scenario, incomplete)
    ready = _ready_checkout(scenario, delivery)
    pix = _pix_checkout(scenario, ready)
    completed = _completed_checkout(scenario, pix)
    checkouts = {
        "incomplete": incomplete,
        "delivery": delivery,
        "ready": ready,
        "pix": pix,
        "completed": completed,
    }
    for checkout in checkouts.values():
        _validate_checkout(checkout, registry)

    protocols = _step_protocols(scenario, profile, card, checkouts)
    order = protocols[8]["order"]
    _validate_schema(order, _ORDER_SCHEMA_URI, registry)
    _validate_schema(
        order,
        f"{_NFE_SCHEMA_URI}#/$defs/br.dev.bcp.shopping.order",
        registry,
    )
    catalog_internal = protocols[2]["internal"]
    catalog_arguments = catalog_internal["request"]["params"]["arguments"]["catalog"]
    catalog_result = catalog_internal["response"]["result"]["structuredContent"]
    _validate_schema(
        catalog_arguments,
        f"{_CATALOG_SEARCH_SCHEMA_URI}#/$defs/search_request",
        registry,
    )
    _validate_schema(
        catalog_result,
        f"{_CATALOG_SEARCH_SCHEMA_URI}#/$defs/search_response",
        registry,
    )
    for protocol in protocols.values():
        if not protocol:
            continue
        request = protocol.get("request")
        response = protocol.get("response")
        if isinstance(request, dict) and "body" in request:
            _validate_a2a_rpc(request)
        if isinstance(response, dict) and response.get("jsonrpc") == "2.0":
            _validate_a2a_rpc(response)

    files: dict[Path, JsonObject] = {}
    step_paths: list[str] = []
    conversation: list[JsonObject] = []
    for number, step in enumerate(scenario["steps"], start=1):
        filename = f"{number:02d}-{step['id'][3:]}.json"
        relative = Path("steps") / filename
        step_paths.append(relative.as_posix())
        conversation.extend(_step_messages(step, scenario))
        files[relative] = {
            "id": step["id"],
            "act": copy.deepcopy(step["act"]),
            "title": copy.deepcopy(step["title"]),
            "narrative": copy.deepcopy(step["narrative"]),
            "conversation": copy.deepcopy(conversation),
            "protocol": protocols[number],
        }
    files[Path("manifest.json")] = {
        "scenario": scenario["id"],
        "protocols": {
            "BCP": scenario["versions"]["bcp"],
            "A2A": scenario["versions"]["a2a"],
        },
        "steps": step_paths,
        "properties": {
            "deterministic": True,
            "network": False,
            "llm": False,
            "auction": False,
            "known_seller": True,
            "direct_pix": True,
        },
        "validation": {
            "bcp": "JSON Schema Draft 2020-12 local",
            "a2a": "A2A SDK 1.x e invariantes do binding JSON-RPC",
        },
    }
    return files


def _encoded(value: JsonObject) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def _write_files(files: Mapping[Path, JsonObject]) -> None:
    STEPS_DIR.mkdir(parents=True, exist_ok=True)
    expected_steps = {SNAPSHOTS_DIR / path for path in files if path.parent == Path("steps")}
    for stale in set(STEPS_DIR.glob("*.json")) - expected_steps:
        stale.unlink()
    for relative, value in files.items():
        destination = SNAPSHOTS_DIR / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(_encoded(value), encoding="utf-8")


def _check_files(files: Mapping[Path, JsonObject]) -> list[str]:
    differences: list[str] = []
    expected_steps = {SNAPSHOTS_DIR / path for path in files if path.parent == Path("steps")}
    existing_steps = set(STEPS_DIR.glob("*.json")) if STEPS_DIR.exists() else set()
    for stale in sorted(existing_steps - expected_steps):
        differences.append(f"unexpected snapshot: {stale.relative_to(PLAYGROUND_DIR)}")
    for relative, value in files.items():
        destination = SNAPSHOTS_DIR / relative
        if not destination.exists():
            differences.append(f"missing snapshot: {destination.relative_to(PLAYGROUND_DIR)}")
        elif destination.read_text(encoding="utf-8") != _encoded(value):
            differences.append(f"outdated snapshot: {destination.relative_to(PLAYGROUND_DIR)}")
    return differences


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic BCP playground snapshots.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate and compare snapshots without writing files",
    )
    arguments = parser.parse_args()
    scenario = _load_json(SCENARIO_PATH)
    files = _build_files(scenario)
    if arguments.check:
        differences = _check_files(files)
        if differences:
            sys.stderr.write("\n".join(differences) + "\n")
            return 1
        sys.stdout.write("playground snapshots are up to date\n")
        return 0
    _write_files(files)
    sys.stdout.write(f"generated {len(files) - 1} playground steps and manifest.json\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
