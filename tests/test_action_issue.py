from gaphor import UML
from gaphor.application import distribution
from gaphor.storage import storage
from gaphor.tests import TestCase
from gaphor.UML.actions import ActionItem, FlowItem


class ActionIssueTestCase(TestCase):
    def test_it(self):
        """Test an issue when loading a freshly created action diagram."""
        ef = self.element_factory
        modeling_language = self.modeling_language
        path = distribution().locate_file("test-models/action-issue.gaphor")
        storage.load(path, ef, modeling_language)

        actions = ef.lselect(UML.Action)
        flows = ef.lselect(UML.ControlFlow)
        assert 3 == len(actions)
        assert 3 == len(flows)

        # Actions live in partitions:
        partitions = ef.lselect(UML.ActivityPartition)
        assert 2 == len(partitions)

        # Okay, so far the data model is saved correctly. Now, how do the
        # handles behave?
        diagrams = ef.lselect(UML.Diagram)
        assert 1 == len(diagrams)

        canvas = diagrams[0].canvas
        assert 9 == len(canvas.get_all_items())
        # Part, Part, Act, Act, Part, Act, Flow, Flow, Flow

        for e in actions + flows:
            assert 1 == len(e.presentation), e
        for i in canvas.select(lambda e: isinstance(e, (FlowItem, ActionItem))):
            assert i.subject, i

        # Loaded as:
        #
        # actions[0] --> flows[0, 1]
        # flows[0, 2] --> actions[2]
        # flows[1] --> actions[1] --> flows[2]

        # start element:
        assert actions[0].outgoing[0] is flows[0]
        assert actions[0].outgoing[1] is flows[1]
        assert not actions[0].incoming

        (cinfo,) = canvas.connections.get_connections(
            handle=flows[0].presentation[0].head
        )
        assert cinfo.connected is actions[0].presentation[0]
        (cinfo,) = canvas.connections.get_connections(
            handle=flows[1].presentation[0].head
        )
        assert cinfo.connected is actions[0].presentation[0]

        # Intermediate element:
        assert actions[1].incoming[0] is flows[1]
        assert actions[1].outgoing[0] is flows[2]

        (cinfo,) = canvas.connections.get_connections(
            handle=flows[1].presentation[0].tail
        )
        assert cinfo.connected is actions[1].presentation[0]
        (cinfo,) = canvas.connections.get_connections(
            handle=flows[2].presentation[0].head
        )
        assert cinfo.connected is actions[1].presentation[0]

        # Final element:
        assert actions[2].incoming[0] is flows[0]
        assert actions[2].incoming[1] is flows[2]

        (cinfo,) = canvas.connections.get_connections(
            handle=flows[0].presentation[0].tail
        )
        assert cinfo.connected is actions[2].presentation[0]
        (cinfo,) = canvas.connections.get_connections(
            handle=flows[2].presentation[0].tail
        )
        assert cinfo.connected is actions[2].presentation[0]

        # Test the parent-child connectivity
        for a in actions:
            (p,) = a.inPartition
            assert p
            assert canvas.get_parent(a.presentation[0])
            assert canvas.get_parent(a.presentation[0]) is p.presentation[0]
