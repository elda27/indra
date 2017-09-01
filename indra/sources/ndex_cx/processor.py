from __future__ import absolute_import, print_function, unicode_literals
from builtins import dict, str
import objectpath
from indra.databases import uniprot_client, chebi_client, hgnc_client
from indra.literature import id_lookup
from indra.statements import *


logger = logging.getLogger('ndex_cx_processor')


_stmt_map = {
    'phosphorylates': Phosphorylation,
    'controls-phosphorylation-of': Phosphorylation,
    'in-complex-with': Complex,
    'NEGATIVE_INFLUENCE': Inhibition,
    'POSITIVE_INFLUENCE': Activation
}


def _get_dict_from_list(dict_key, list_of_dicts):
    """Retrieve a specific dict from a list of dicts.

    Parameters
    ----------
    dict_key : str
        The (single) key of the dict to be retrieved from the list.
    list_of_dicts : list
        The list of dicts to search for the specific dict.

    Returns
    -------
    dict value
        The value associated with the dict_key (e.g., a list of nodes or
        edges).
    """
    the_dict = [cur_dict for cur_dict in list_of_dicts
                if cur_dict.get(dict_key)]
    if not the_dict:
        raise ValueError('Could not find a dict with key %s' % dict_key)
    return the_dict[0][dict_key]


class NdexCxProcessor(object):
    """The NdexCxProcessor extracts INDRA Statements from Cytoscape CX JSON.

    Parameters
    ----------
    cx : list of dicts
        JSON content containing the Cytoscape network in CX format.

    Attributes
    ----------
    statements : list
        A list of extracted INDRA Statements. Not all edges in the network
        may be converted into Statements.
    """
    def __init__(self, cx):
        self.cx = cx
        self.statements = []
        # Initialize the dict mapping node IDs to gene names
        self._node_names = {}
        self._node_agents = {}
        self._initialize_node_agents()

    def _initialize_node_agents(self):
        """Initialize internal dicts containing node information."""
        nodes = _get_dict_from_list('nodes', self.cx)
        invalid_genes = []
        for node in nodes:
            id = node['@id']
            node_name = node['n']
            self._node_names[id] = node_name
            hgnc_id = hgnc_client.get_hgnc_id(node_name)
            if not hgnc_id:
                invalid_genes.append(node_name)
            else:
                up_id = hgnc_client.get_uniprot_id(hgnc_id)
                assert up_id
                self._node_agents[id] = Agent(node_name,
                                              db_refs={'HGNC': hgnc_id,
                                                       'UP': up_id})
        logger.info('Skipped invalid gene symbols: %s' %
                    ', '.join(invalid_genes))

    def get_agents(self):
        """Get list of grounded nodes in the network as Agents.

        Returns
        -------
        list of Agents
            Only nodes containing sufficient information to be grounded will
            be contained in this list.
        """
        return [ag for ag in self._node_agents.values()]

    def get_node_names(self):
        """Get list of all nodes in the network by name."""
        return [name for name in self._node_names.values()]

    def get_statements(self):
        """Convert network edges into Statements.

        Returns
        -------
        list of Statements
            Converted INDRA Statements.
        """
        edges = _get_dict_from_list('edges', self.cx)
        for edge in edges:
            edge_type = edge.get('i')
            if not edge_type:
                continue
            stmt_type = _stmt_map.get(edge_type)
            if stmt_type:
                id = edge['@id']
                source_agent = self._node_agents.get(edge['s'])
                target_agent = self._node_agents.get(edge['t'])
                if not source_agent or not target_agent:
                    logger.info("Skipping edge %s->%s: %s" %
                                (self._node_names[edge['s']],
                                 self._node_names[edge['t']], edge))
                    continue
                if stmt_type == Complex:
                    stmt = stmt_type([source_agent, target_agent])
                else:
                    stmt = stmt_type(source_agent, target_agent)
                self.statements.append(stmt)
        return self.statements

