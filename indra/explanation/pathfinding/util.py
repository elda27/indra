__all__ = ['path_sign_to_signed_nodes', 'signed_nodes_to_signed_edge',
           'get_sorted_neighbors']
import logging
import networkx as nx

logger = logging.getLogger(__name__)


def path_sign_to_signed_nodes(source, target, edge_sign):
    """Translates a signed edge or path to valid signed nodes

    Pairs with a negative source node are filtered out.

    Parameters
    ----------
    source : str|int
        The source node
    target : str|int
        The target node
    edge_sign : int
        The sign of the edge

    Returns
    -------
    sign_tuple : (a, sign), (b, sign)
        Tuple of tuples of the valid combination of signed nodes
    """
    # Sign definitions: + == 0, - == 1
    # + path -> (a+, b+)
    # - path -> (a+, b-)
    # (a-, b-) and (a-, b+) are also technically valid but not in this context
    try:
        if int(edge_sign) == 0:
            return (source, 0), (target, 0)
        else:
            return (source, 1), (target, 0)
    except ValueError:
        logger.warning('Invalid sign %s when translating edge sign to int'
                       % edge_sign)
        return (None, None), (None, None)


def signed_nodes_to_signed_edge(source, target):
    """Create the triple (node, node, sign) from a pair of signed nodes

    Assuming source, target forms an edge of signed nodes:
    edge = (a, sign), (b, sign), return the corresponding signed edge triple

    Parameters
    ----------
    source : tuple(str|int, sign)
        A valid signed node
    target : tuple(str|int, sign)
        A valid signed node

    Returns
    -------
    tuple
        A tuple, (source, target, sign), representing the corresponding
        signed edge.
    """
    # Sign definitions: + == 0, - == 1
    # + edge/path -> (a+, b+) and (a-, b-)
    # - edge/path -> (a-, b+) and (a+, b-)
    source_name, source_sign = source
    target_name, target_sign = target
    try:
        if int(source_sign) == int(target_sign):
            return source_name, target_name, 0
        else:
            return source_name, target_name, 1
    except ValueError:
        logger.warning('Error translating signed nodes to signed edge using '
                       '(%s, %s)' % (source, target))
        return None, None, None


def get_sorted_neighbors(G, node, reverse, force_edges=None):
    """Sort the returned neighbors in descending order by belief

    Parameters
    ----------
    G : nx.DiGraph
        A networkx DiGraph
    node : str|int
        A valid networkx node name
    reverse : bool
        Indicates direction of search. Neighbors are either successors
        (downstream search) or predecessors (reverse search).
    force_edges : list
        A list of allowed edges. If provided, only allow neighbors that
        can be reached by the allowed edges.
    """
    if reverse:
        if force_edges:
            neighbors = list(e[0] for e in set(G.in_edges(
                node)).intersection(set(force_edges)))
        else:
            neighbors = G.predecessors(node)
        return sorted(
            neighbors,
            key=lambda n:
                G.edges[(n, node)].get('belief', 0),
            reverse=True
        )
    else:
        if force_edges:
            neighbors = list(e[1] for e in set(G.out_edges(
                node)).intersection(set(force_edges)))
        else:
            neighbors = G.successors(node)
        return sorted(
            neighbors,
            key=lambda n:
                G.edges[(node, n)].get('belief', 0),
            reverse=True)


edge_filter_functions = {}
# Need to set a global G variable for filter edge function to work
G = None


def register_edge_filter(function):
    """
    Decorator to register a function as an edge filter for getting subgraphs.
    Edge filter function should take two (u, v - for DiGraph) or three
    (u, v, k -  for MultiDiGraph) parameters and return True if the edge
    should be in the graph and False otherwise.
    """
    edge_filter_functions[function.__name__] = function
    return function


def get_subgraph(g, filter_func_name):
    """Get a subgraph of original graph filtered by a provided function."""
    # Updating global variable here to handle NetworkX implementation of
    # closures used in subgraph_view
    global G
    G = g
    filter_edge = edge_filter_functions.get(filter_func_name)
    view = nx.subgraph_view(g, filter_edge=filter_edge)
    # Copying to get a graph object instead of view
    new_g = view.copy()
    return new_g


@register_edge_filter
def filter_to_internal_edges(u, v, *args):
    if args:
        edge = G[u][v][args[0]]
    else:
        edge = G[u][v]
    for stmts_dict in edge['statements']:
        if stmts_dict['internal']:
            return True
    return False
