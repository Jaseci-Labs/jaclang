"""Test for jaseci plugin."""

import io
import os
import sys

from jaclang import jac_import as orig_jac_import
from jaclang.cli import cli
from jaclang.core.constructs import ExecutionContext
from jaclang.core.context import EXECUTION_CONTEXT
from jaclang.utils.test import TestCase

loaded_mod: dict[str, object] = {}
session = None


def close(self: ExecutionContext) -> None:
    """Override close for testing."""
    self.datasource.close()
    if shelf := self.datasource.__shelf__:
        shelf.close()
    EXECUTION_CONTEXT.set(None)


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

        self._close = ExecutionContext.close
        ExecutionContext.close = close  # type: ignore
        cli.jac_import = jac_import  # type: ignore

        if jctx := EXECUTION_CONTEXT.get(None):
            jctx.close()

    def tearDown(self) -> None:
        """Tear down test."""
        super().tearDown()
        sys.stdout = sys.__stdout__
        ExecutionContext.close = self._close  # type: ignore
        cli.jac_import = orig_jac_import

    def _output2buffer(self) -> None:
        """Start capturing output."""
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def _output2std(self) -> None:
        """Redirect output back to stdout."""
        sys.stdout = sys.__stdout__

    def _del_session(self, session: str) -> None:
        if os.path.exists(session):
            os.remove(session)

    def test_walker_simple_persistent(self) -> None:
        """Test simple persistent object."""
        global session
        session = self.fixture_abs_path("test_walker_simple_persistent.session")
        self._output2buffer()
        cli.run(
            filename=self.fixture_abs_path("simple_persistent.jac"),
            session=session,
            walker="create",
        )
        cli.run(
            filename=self.fixture_abs_path("simple_persistent.jac"),
            session=session,
            walker="traverse",
        )
        output = self.capturedOutput.getvalue().strip()
        self.assertEqual(output, "node a\nnode b")
        self._del_session(session)

    def test_entrypoint_root(self) -> None:
        """Test entrypoint being root."""
        global session
        session = self.fixture_abs_path("test_entrypoint_root.session")
        cli.run(
            filename=self.fixture_abs_path("simple_persistent.jac"),
            session=session,
            walker="create",
        )
        obj = cli.get_object(session=session, id="root")
        self._output2buffer()
        cli.run(
            filename=self.fixture_abs_path("simple_persistent.jac"),
            session=session,
            node=f"n::{obj['id']}",
            walker="traverse",
        )
        output = self.capturedOutput.getvalue().strip()
        self.assertEqual(output, "node a\nnode b")
        self._del_session(session)

    def test_entrypoint_non_root(self) -> None:
        """Test entrypoint being non root node."""
        global session
        session = self.fixture_abs_path("test_entrypoint_non_root.session")
        cli.run(
            filename=self.fixture_abs_path("simple_persistent.jac"),
            session=session,
            walker="create",
        )
        obj = cli.get_object(session=session, id="root")
        edge_obj = cli.get_object(session=session, id=obj["edges"][0].ref_id)
        a_obj = cli.get_object(session=session, id=edge_obj["target"].ref_id)

        self._output2buffer()
        cli.run(
            filename=self.fixture_abs_path("simple_persistent.jac"),
            session=session,
            node=f"n:a:{a_obj['id']}",
            walker="traverse",
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
        edge_objs = [cli.get_object(session=session, id=e.ref_id) for e in obj["edges"]]
        node_ids = [obj["target"].ref_id for obj in edge_objs]
        node_objs = [cli.get_object(session=session, id=n_id) for n_id in node_ids]
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
        cli.run(
            filename=self.fixture_abs_path("simple_node_connection.jac"),
            session=session,
            walker="filter_on_edge_get_edge",
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
        cli.run(
            filename=self.fixture_abs_path("simple_node_connection.jac"),
            session=session,
            walker="filter_on_edge_get_node",
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
        cli.run(
            filename=self.fixture_abs_path("simple_node_connection.jac"),
            session=session,
            walker="filter_on_node_get_node",
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
        cli.run(
            filename=self.fixture_abs_path("simple_node_connection.jac"),
            session=session,
            walker="filter_on_edge_visit",
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
        cli.run(
            filename=self.fixture_abs_path("simple_node_connection.jac"),
            session=session,
            walker="filter_on_node_visit",
        )
        self.assertEqual(self.capturedOutput.getvalue().strip(), "simple(tag='first')")
        self._del_session(session)

    def test_indirect_reference_node(self) -> None:
        """Test reference node indirectly without visiting."""
        global session
        session = self.fixture_abs_path("test_indirect_reference_node.session")
        cli.run(
            filename=self.fixture_abs_path("simple_persistent.jac"),
            session=session,
            walker="create",
        )
        self._output2buffer()
        cli.run(
            filename=self.fixture_abs_path("simple_persistent.jac"),
            session=session,
            walker="indirect_ref",
        )
        self.assertEqual(
            self.capturedOutput.getvalue().strip(),
            "[b(name='node b')]\n[GenericEdge]",
        )
        self._del_session(session)
