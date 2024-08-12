"""Test for jaseci plugin."""

import io
import os
import sys

from jaclang import jac_import as orig_jac_import
from jaclang.cli import cli
from jaclang.runtimelib.constructs import EdgeArchitype, NodeArchitype
from jaclang.utils.test import TestCase

loaded_mod: dict[str, object] = {}
session = None


def jac_import(target: str, base_path: str, **kwargs) -> object:  # noqa: ANN003
    """Override jac importing to do it only once per session per file."""
    path = f"{session}:{target}/{base_path}"
    if load := loaded_mod.get(path):
        return load

    load = loaded_mod[path] = orig_jac_import(
        target=target, base_path=base_path, **kwargs
    )
    return load


class TestJaseciPlugin(TestCase):
    """Test jaseci plugin."""

    def setUp(self) -> None:
        """Set up test."""
        super().setUp()
        cli.jac_import = jac_import  # type: ignore
        EdgeArchitype.__jac_classes__ = {}
        NodeArchitype.__jac_classes__ = {}

    def tearDown(self) -> None:
        """Tear down test."""
        super().tearDown()
        sys.stdout = sys.__stdout__
        cli.jac_import = orig_jac_import

    def _output2buffer(self) -> None:
        """Start capturing output."""
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def _output2std(self) -> None:
        """Redirect output back to stdout."""
        sys.stdout = sys.__stdout__

    def _del_session(self, session: str) -> None:
        path = os.path.dirname(session)
        prefix = os.path.basename(session)
        for file in os.listdir(path):
            if file.startswith(prefix):
                os.remove(f"{path}/{file}")

    def test_walker_simple_persistent(self) -> None:
        """Test simple persistent object."""
        global session
        session = self.fixture_abs_path("test_walker_simple_persistent.session")
        self._output2buffer()
        cli.enter(
            filename=self.fixture_abs_path("simple_persistent.jac"),
            session=session,
            entrypoint="create",
        )
        cli.enter(
            filename=self.fixture_abs_path("simple_persistent.jac"),
            session=session,
            entrypoint="traverse",
        )
        output = self.capturedOutput.getvalue().strip()
        self.assertEqual(output, "node a\nnode b")
        self._del_session(session)

    def test_entrypoint_root(self) -> None:
        """Test entrypoint being root."""
        global session
        session = self.fixture_abs_path("test_entrypoint_root.session")
        cli.enter(
            filename=self.fixture_abs_path("simple_persistent.jac"),
            session=session,
            entrypoint="create",
        )
        obj = cli.get_object(session=session, id="root")
        self._output2buffer()
        cli.enter(
            filename=self.fixture_abs_path("simple_persistent.jac"),
            session=session,
            node=f"n::{obj['id']}",
            entrypoint="traverse",
        )
        output = self.capturedOutput.getvalue().strip()
        self.assertEqual(output, "node a\nnode b")
        self._del_session(session)

    def test_entrypoint_non_root(self) -> None:
        """Test entrypoint being non root node."""
        global session
        session = self.fixture_abs_path("test_entrypoint_non_root.session")
        cli.enter(
            filename=self.fixture_abs_path("simple_persistent.jac"),
            session=session,
            entrypoint="create",
        )
        obj = cli.get_object(session=session, id="root")
        edge_obj = cli.get_object(session=session, id=obj["edges"][0])
        a_obj = cli.get_object(session=session, id=edge_obj["target"])

        self._output2buffer()
        cli.enter(
            filename=self.fixture_abs_path("simple_persistent.jac"),
            session=session,
            node=f"n:a:{a_obj['id']}",
            entrypoint="traverse",
        )
        output = self.capturedOutput.getvalue().strip()
        self.assertEqual(output, "node a\nnode b")
        self._del_session(session)

    def test_get_edge(self) -> None:
        """Test get an edge object."""
        global session
        session = self.fixture_abs_path("test_get_edge.session")
        cli.run(
            filename=self.fixture_abs_path("simple_node_connection.jac"),
            session=session,
        )
        obj = cli.get_object(session=session, id="root")
        self.assertEqual(len(obj["edges"]), 2)
        edge_objs = [cli.get_object(session=session, id=e) for e in obj["edges"]]
        node_objs = [
            cli.get_object(session=session, id=edge["target"]) for edge in edge_objs
        ]
        self.assertEqual(len(node_objs), 2)
        self.assertEqual(
            {obj["architype"]["tag"] for obj in node_objs}, {"first", "second"}
        )
        self._del_session(session)

    def test_filter_on_edge_get_edge(self) -> None:
        """Test filtering on edge."""
        global session
        session = self.fixture_abs_path("test_filter_on_edge_get_edge.session")
        cli.run(
            filename=self.fixture_abs_path("simple_node_connection.jac"),
            session=session,
        )
        self._output2buffer()
        cli.enter(
            filename=self.fixture_abs_path("simple_node_connection.jac"),
            session=session,
            entrypoint="filter_on_edge_get_edge",
        )
        self.assertEqual(
            self.capturedOutput.getvalue().strip(), "[simple_edge(index=1)]"
        )
        self._del_session(session)

    def test_filter_on_edge_get_node(self) -> None:
        """Test filtering on edge, then get node."""
        global session
        session = self.fixture_abs_path("test_filter_on_edge_get_node.session")
        cli.run(
            filename=self.fixture_abs_path("simple_node_connection.jac"),
            session=session,
        )
        self._output2buffer()
        cli.enter(
            filename=self.fixture_abs_path("simple_node_connection.jac"),
            session=session,
            entrypoint="filter_on_edge_get_node",
        )
        self.assertEqual(
            self.capturedOutput.getvalue().strip(), "[simple(tag='second')]"
        )
        self._del_session(session)

    def test_filter_on_node_get_node(self) -> None:
        """Test filtering on node, then get edge."""
        global session
        session = self.fixture_abs_path("test_filter_on_node_get_node.session")
        cli.run(
            filename=self.fixture_abs_path("simple_node_connection.jac"),
            session=session,
        )
        self._output2buffer()
        cli.enter(
            filename=self.fixture_abs_path("simple_node_connection.jac"),
            session=session,
            entrypoint="filter_on_node_get_node",
        )
        self.assertEqual(
            self.capturedOutput.getvalue().strip(), "[simple(tag='second')]"
        )
        self._del_session(session)

    def test_filter_on_edge_visit(self) -> None:
        """Test filtering on edge, then visit."""
        global session
        session = self.fixture_abs_path("test_filter_on_edge_visit.session")
        cli.run(
            filename=self.fixture_abs_path("simple_node_connection.jac"),
            session=session,
        )
        self._output2buffer()
        cli.enter(
            filename=self.fixture_abs_path("simple_node_connection.jac"),
            session=session,
            entrypoint="filter_on_edge_visit",
        )
        self.assertEqual(self.capturedOutput.getvalue().strip(), "simple(tag='first')")
        self._del_session(session)

    def test_filter_on_node_visit(self) -> None:
        """Test filtering on node, then visit."""
        global session
        session = self.fixture_abs_path("test_filter_on_node_visit.session")
        cli.run(
            filename=self.fixture_abs_path("simple_node_connection.jac"),
            session=session,
        )
        self._output2buffer()
        cli.enter(
            filename=self.fixture_abs_path("simple_node_connection.jac"),
            session=session,
            entrypoint="filter_on_node_visit",
        )
        self.assertEqual(self.capturedOutput.getvalue().strip(), "simple(tag='first')")
        self._del_session(session)

    def test_indirect_reference_node(self) -> None:
        """Test reference node indirectly without visiting."""
        global session
        session = self.fixture_abs_path("test_indirect_reference_node.session")
        cli.enter(
            filename=self.fixture_abs_path("simple_persistent.jac"),
            session=session,
            entrypoint="create",
        )
        self._output2buffer()
        cli.enter(
            filename=self.fixture_abs_path("simple_persistent.jac"),
            session=session,
            entrypoint="indirect_ref",
        )
        self.assertEqual(
            self.capturedOutput.getvalue().strip(),
            "[b(name='node b')]\n[GenericEdge()]",
        )
        self._del_session(session)

    def trigger_access_validation_test(
        self, give_access_to_full_graph: bool, via_all: bool = False
    ) -> None:
        """Test different access validation."""
        self._output2buffer()

        ##############################################
        #              ALLOW READ ACCESS             #
        ##############################################

        node_1 = "" if give_access_to_full_graph else self.nodes[0]
        node_2 = "" if give_access_to_full_graph else self.nodes[1]

        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="allow_other_root_access",
            root=self.roots[0],
            node=node_1,
            args=[self.roots[1], 0, via_all],
        )
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="allow_other_root_access",
            root=self.roots[1],
            node=node_2,
            args=[self.roots[0], 0, via_all],
        )

        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="update_node",
            root=self.roots[0],
            node=self.nodes[1],
            args=[20],
        )
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="update_node",
            root=self.roots[1],
            node=self.nodes[0],
            args=[10],
        )

        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="check_node",
            root=self.roots[0],
            node=self.nodes[1],
        )
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="check_node",
            root=self.roots[1],
            node=self.nodes[0],
        )
        archs = self.capturedOutput.getvalue().strip().split("\n")
        self.assertTrue(len(archs) == 2)

        # --------- NO UPDATE SHOULD HAPPEN -------- #

        self.assertTrue(archs[0], "A(val=2)")
        self.assertTrue(archs[1], "A(val=1)")

        self._output2buffer()
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="disallow_other_root_access",
            root=self.roots[0],
            node=node_1,
            args=[self.roots[1], via_all],
        )
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="disallow_other_root_access",
            root=self.roots[1],
            node=node_2,
            args=[self.roots[0], via_all],
        )

        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="check_node",
            root=self.roots[0],
            node=self.nodes[1],
        )
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="check_node",
            root=self.roots[1],
            node=self.nodes[0],
        )
        self.assertFalse(self.capturedOutput.getvalue().strip())

        ##############################################
        #             ALLOW WRITE ACCESS             #
        ##############################################

        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="allow_other_root_access",
            root=self.roots[0],
            node=node_1,
            args=[self.roots[1], "WRITE", via_all],
        )
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="allow_other_root_access",
            root=self.roots[1],
            node=node_2,
            args=[self.roots[0], "WRITE", via_all],
        )

        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="update_node",
            root=self.roots[0],
            node=self.nodes[1],
            args=[20],
        )
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="update_node",
            root=self.roots[1],
            node=self.nodes[0],
            args=[10],
        )

        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="check_node",
            root=self.roots[0],
            node=self.nodes[1],
        )
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="check_node",
            root=self.roots[1],
            node=self.nodes[0],
        )
        archs = self.capturedOutput.getvalue().strip().split("\n")
        self.assertTrue(len(archs) == 2)

        # --------- UPDATE SHOULD HAPPEN -------- #

        self.assertTrue(archs[0], "A(val=20)")
        self.assertTrue(archs[1], "A(val=10)")

        self._output2buffer()
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="disallow_other_root_access",
            root=self.roots[0],
            node=node_1,
            args=[self.roots[1], via_all],
        )
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="disallow_other_root_access",
            root=self.roots[1],
            node=node_2,
            args=[self.roots[0], via_all],
        )

        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="check_node",
            root=self.roots[0],
            node=self.nodes[1],
        )
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="check_node",
            root=self.roots[1],
            node=self.nodes[0],
        )
        self.assertFalse(self.capturedOutput.getvalue().strip())

    def test_other_root_access(self) -> None:
        """Test filtering on node, then visit."""
        global session
        session = self.fixture_abs_path("other_root_access.session")

        ##############################################
        #                CREATE ROOTS                #
        ##############################################

        self._output2buffer()
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="create_other_root",
        )
        root1 = self.capturedOutput.getvalue().strip()

        self._output2buffer()
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="create_other_root",
        )
        root2 = self.capturedOutput.getvalue().strip()

        ##############################################
        #           CREATE RESPECTIVE NODES          #
        ##############################################

        self._output2buffer()
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="create_node",
            root=root1,
            args=[1],
        )
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="create_node",
            root=root2,
            args=[2],
        )
        nodes = self.capturedOutput.getvalue().strip().split("\n")
        self.assertTrue(len(nodes) == 2)
        self.assertTrue(nodes[0].startswith("n:A:"))
        self.assertTrue(nodes[1].startswith("n:A:"))

        ##############################################
        #           VISIT RESPECTIVE NODES           #
        ##############################################

        self._output2buffer()
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="check_node",
            root=root1,
        )
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="check_node",
            root=root2,
        )
        archs = self.capturedOutput.getvalue().strip().split("\n")
        self.assertTrue(len(archs) == 2)
        self.assertTrue(archs[0], "A(val=1)")
        self.assertTrue(archs[1], "A(val=2)")

        ##############################################
        #              SWAP TARGET NODE              #
        #                  NO ACCESS                 #
        ##############################################

        self._output2buffer()
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="check_node",
            root=root1,
            node=nodes[1],
        )
        cli.enter(
            filename=self.fixture_abs_path("other_root_access.jac"),
            session=session,
            entrypoint="check_node",
            root=root2,
            node=nodes[0],
        )
        self.assertFalse(self.capturedOutput.getvalue().strip())

        ##############################################
        #        TEST DIFFERENT ACCESS OPTIONS       #
        ##############################################

        self.roots = [root1, root2]
        self.nodes = nodes

        self.trigger_access_validation_test(give_access_to_full_graph=False)
        self.trigger_access_validation_test(give_access_to_full_graph=True)

        self.trigger_access_validation_test(
            give_access_to_full_graph=False, via_all=True
        )
        self.trigger_access_validation_test(
            give_access_to_full_graph=True, via_all=True
        )

        self._del_session(session)
