import pytest
from gaphas.aspect import ConnectionSink, Connector

from gaphor import UML
from gaphor.application import Application
from gaphor.core import Transaction
from gaphor.UML.classes import AssociationItem, ClassItem


@pytest.fixture
def application():
    app = Application()
    yield app
    app.shutdown()


@pytest.fixture
def session(application):
    return application.new_session()


@pytest.fixture
def event_manager(session):
    return session.get_service("event_manager")


@pytest.fixture
def element_factory(session):
    return session.get_service("element_factory")


@pytest.fixture
def undo_manager(session):
    return session.get_service("undo_manager")


def connect(line, handle, item, port=None):
    """Connect line's handle to an item.

    If port is not provided, then first port is used.
    """
    canvas = line.canvas
    assert canvas is item.canvas
    if port is None and len(item.ports()) > 0:
        port = item.ports()[0]

    sink = ConnectionSink(item, port)
    connector = Connector(line, handle, canvas.connections)

    connector.connect(sink)

    cinfo = canvas.get_connection(handle)
    assert cinfo.connected is item
    assert cinfo.port is port


def test_class_association_undo_redo(event_manager, element_factory, undo_manager):
    diagram = element_factory.create(UML.Diagram)

    assert 0 == len(diagram.canvas.solver.constraints)

    ci1 = diagram.create(ClassItem, subject=element_factory.create(UML.Class))
    assert 6 == len(diagram.canvas.solver.constraints)

    ci2 = diagram.create(ClassItem, subject=element_factory.create(UML.Class))
    assert 12 == len(diagram.canvas.solver.constraints)

    a = diagram.create(AssociationItem)

    connect(a, a.head, ci1)
    connect(a, a.tail, ci2)

    # Diagram, Association, 2x Class, Property, LiteralSpecification
    assert 6 == len(element_factory.lselect())
    assert 14 == len(diagram.canvas.solver.constraints)

    undo_manager.clear_undo_stack()
    assert not undo_manager.can_undo()

    with Transaction(event_manager):
        ci2.unlink()

    assert undo_manager.can_undo()

    def get_connected(handle):
        """Get item connected to line via handle."""
        cinfo = diagram.canvas.get_connection(handle)
        if cinfo:
            return cinfo.connected
        return None

    assert ci1 == get_connected(a.head)
    assert None is get_connected(a.tail)

    for i in range(3):
        assert 7 == len(diagram.canvas.solver.constraints)

        undo_manager.undo_transaction()

        assert 14 == len(diagram.canvas.solver.constraints)

        assert ci1 == get_connected(a.head)
        assert ci2 == get_connected(a.tail)

        undo_manager.redo_transaction()


def test_diagram_item_should_not_end_up_in_element_factory(
    event_manager, element_factory, undo_manager
):
    diagram = element_factory.create(UML.Diagram)

    with Transaction(event_manager):
        cls = diagram.create(ClassItem, subject=element_factory.create(UML.Class))

    undo_manager.undo_transaction()
    undo_manager.redo_transaction()

    assert cls not in element_factory.lselect(), element_factory.lselect()


def test_deleted_diagram_item_should_not_end_up_in_element_factory(
    event_manager, element_factory, undo_manager
):
    diagram = element_factory.create(UML.Diagram)
    cls = diagram.create(ClassItem, subject=element_factory.create(UML.Class))

    with Transaction(event_manager):
        cls.unlink()

    undo_manager.undo_transaction()

    assert cls not in element_factory.lselect(), element_factory.lselect()

    undo_manager.redo_transaction()

    assert cls not in element_factory.lselect(), element_factory.lselect()
