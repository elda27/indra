import os

from indra.statements import *
from indra.statements import Agent
from indra.sources.gnbr.processor import GnbrProcessor
import indra.sources.gnbr.api as api


def test_standardize_agent():
    agent = GnbrProcessor.standardize_agent('xxx', '673')
    assert isinstance(agent, Agent)
    assert agent.name == 'BRAF'
    assert agent.db_refs.get('TEXT') == 'xxx'
    assert agent.db_refs.get('EGID') == '673'
    assert agent.db_refs.get('HGNC') == '1097'


def test_process_gene_gene():
    test_path1: str = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'gnbr_gene_gene_part1_test.tsv')
    test_path2: str = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'gnbr_gene_gene_part2_test.tsv')
    gp = api.process_gene_gene(test_path1, test_path2)
    assert len(gp.statements) != 0
    assert isinstance(gp, GnbrProcessor)
    assert gp.first_type == 'gene'
    assert gp.second_type == 'gene'
    assert isinstance(gp.statements[0], Activation)
    assert isinstance(gp.statements[1], Activation)
    assert isinstance(gp.statements[2], IncreaseAmount)
    assert isinstance(gp.statements[3], IncreaseAmount)
    assert isinstance(gp.statements[4], Complex)


def test_process_chemical_gene():
    test_path1: str = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'gnbr_chemical_gene_part1_test.tsv')
    test_path2: str = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'gnbr_chemical_gene_part2_test.tsv')
    gp = api.process_chemical_gene(test_path1, test_path2)
    assert len(gp.statements) != 0
    assert isinstance(gp, GnbrProcessor)
    assert gp.first_type == 'chemical'
    assert gp.second_type == 'gene'
    assert isinstance(gp.statements[0], Activation)
    assert isinstance(gp.statements[1], Inhibition)
