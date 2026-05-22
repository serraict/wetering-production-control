"""Steps that drive operator actions on the PC web app.

We bypass NiceGUI and call PottingLineController.set_active_lot
directly (same call ActivePottingLotService makes in production).
Keeps the test focused on the OPC contract.
"""

from behave import given, when

from production_control.config.opc_config import OPCConfig
from production_control.potting_lots.line_controller import PottingLineController


def _controller(context):
    if not hasattr(context, "line_controller"):
        config = OPCConfig(
            endpoint="opc.tcp://127.0.0.1:4840",
            connection_timeout=5,
            retry_attempts=2,
            retry_delay=0.1,
        )
        context.line_controller = PottingLineController(config=config, secure=False)
    return context.line_controller


def _run(coro):
    import asyncio

    return asyncio.run(coro)


@when("the operator activates partij {partij:d} on line {line:d}")
def step_operator_activates(context, partij, line):
    success = _run(_controller(context).set_active_lot(line, partij))
    assert success, f"set_active_lot({line}, {partij}) failed"


@when("the operator deactivates line {line:d}")
def step_operator_deactivates(context, line):
    success = _run(_controller(context).set_active_lot(line, 0))
    assert success, f"set_active_lot({line}, 0) failed"


@given("partij {partij:d} is active on line {line:d}")
def step_given_partij_active(context, partij, line):
    success = _run(_controller(context).set_active_lot(line, partij))
    assert success, f"set_active_lot({line}, {partij}) failed"
