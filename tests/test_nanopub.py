from unittest.mock import patch

import pytest
import rdflib
import requests
from rdflib.namespace import RDF

from nanopub import NanopubClient, namespaces
from nanopub.nanopub import Nanopub, NANOPUB_TEST_SERVER

skip_if_nanopub_server_unavailable = (
    pytest.mark.skipif(requests.get(NANOPUB_TEST_SERVER).status_code != 200,
                       reason='Nanopub server is unavailable'))

client = NanopubClient()


@pytest.mark.flaky(max_runs=10)
@skip_if_nanopub_server_unavailable
def test_nanopub_search_text():
    """
    Check that Nanopub text search is returning results for a few common search terms
    """
    searches = ['fair', 'heart']

    for search in searches:
        results = client.search_text(search)
        assert len(results) > 0

    assert len(client.search_text('')) == 0


@pytest.mark.flaky(max_runs=10)
@skip_if_nanopub_server_unavailable
def test_nanopub_search_pattern():
    """
        Check that Nanopub pattern search is returning results
    """
    searches = [
        ('', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'https://www.omg.org/spec/BPMN/scriptTask'),
        ('http://purl.org/np/RANhYfdZCVDQr8ItxDYCZWhvBhzjJTs9Cq-vPnmSBDd5g', '', '')
    ]

    for subj, pred, obj in searches:
        results = client.search_pattern(subj=subj, pred=pred, obj=obj)
        assert len(results) > 0
        assert 'Error' not in results[0]


@pytest.mark.flaky(max_runs=10)
@skip_if_nanopub_server_unavailable
def test_nanopub_search_things():
    """
        Check that Nanopub 'things' search is returning results
    """
    searches = [
        'http://dkm.fbk.eu/index.php/BPMN2_Ontology#ManualTask',
        'http://purl.org/net/p-plan#Plan'
    ]

    for thing_type in searches:
        results = client.search_things(type=thing_type)
        assert len(results) > 0

    with pytest.raises(Exception):
        client.search_things()


def test_grlc_url():
    result = client._grlc_url('http://test.nl', 'search')
    assert result == 'http://test.nl/api/local/local/search'


def test_nanopub_search():
    with pytest.raises(Exception):
        client._search(params=None,
                       max_num_results=100,
                       endpoint='http://www.api.url')
    with pytest.raises(Exception):
        client._search(params={'search': 'text'},
                       max_num_results=None,
                       endpoint='http://www.api.url')
    with pytest.raises(Exception):
        client._search(params={'search': 'text'},
                       max_num_results=100,
                       endpoint=None)


@pytest.mark.flaky(max_runs=10)
@skip_if_nanopub_server_unavailable
def test_nanopub_fetch():
    """
        Check that Nanopub fetch is returning results for a few known nanopub URIs.
        Check that the returned object is of type NNanopubObj, that it has the expected
        source_uri, and that it has non-zero data.
    """
    known_nps = [
        'http://purl.org/np/RAFNR1VMQC0AUhjcX2yf94aXmG1uIhteGXpq12Of88l78',
        'http://purl.org/np/RAePO1Fi2Wp1ARk2XfOnTTwtTkAX1FBU3XuCwq7ng0jIo',
        'http://purl.org/np/RA48Iprh_kQvb602TR0ammkR6LQsYHZ8pyZqZTPQIl17s'
    ]

    for np_uri in known_nps:
        np = client.fetch(np_uri, format='trig')
        assert isinstance(np, Nanopub)
        assert np.source_uri == np_uri
        assert len(np.rdf) > 0
        assert np.assertion is not None
        assert np.pubinfo is not None
        assert np.provenance is not None
        assert len(np.__str__()) > 0


def test_nanopub_from_assertion():
    """
    Test that Nanopub.from_assertion is creating an rdf graph with the right features (contexts)
    for a nanopub.
    """
    assertion_rdf = rdflib.Graph()
    assertion_rdf.add((namespaces.AUTHOR.DrBob, namespaces.HYCL.claims,
                       rdflib.Literal('This is a test')))

    nanopub = Nanopub.from_assertion(assertion_rdf)

    assert nanopub.rdf is not None
    assert (None, RDF.type, namespaces.NP.Nanopublication) in nanopub.rdf
    assert (None, namespaces.NP.hasAssertion, None) in nanopub.rdf
    assert (None, namespaces.NP.hasProvenance, None) in nanopub.rdf
    assert (None, namespaces.NP.hasPublicationInfo, None) in nanopub.rdf

    new_concept = rdflib.term.URIRef('www.purl.org/new/concept/test')
    nanopub = Nanopub.from_assertion(assertion_rdf, introduces_concept=new_concept)

    assert nanopub.rdf is not None
    assert (None, RDF.type, namespaces.NP.Nanopublication) in nanopub.rdf
    assert (None, namespaces.NP.hasAssertion, None) in nanopub.rdf
    assert (None, namespaces.NP.hasProvenance, None) in nanopub.rdf
    assert (None, namespaces.NP.hasPublicationInfo, None) in nanopub.rdf

    assert (None, namespaces.NPX.introduces, new_concept) in nanopub.rdf


@patch('nanopub.java_wrapper.publish')
def test_nanopub_claim(java_wrapper_publish_mock):
    client = NanopubClient()
    optional_triple = (rdflib.term.URIRef('http://www.uri1.com'),
                       rdflib.term.URIRef('http://www.uri2.com'),
                       rdflib.Literal('Something'))
    client.claim('Some controversial statement', rdftriple=optional_triple)


@patch('nanopub.java_wrapper.publish')
def test_nanopub_publish(java_wrapper_publish_mock):
    client = NanopubClient()
    assertion_rdf = rdflib.Graph()
    assertion_rdf.add((namespaces.AUTHOR.DrBob, namespaces.HYCL.claims, rdflib.Literal('This is a test')))

    nanopub = Nanopub.from_assertion(
        assertion_rdf=assertion_rdf,
        uri=rdflib.term.URIRef('http://www.example.com/auri'),
        introduces_concept=namespaces.AUTHOR.DrBob,
        derived_from=rdflib.term.URIRef('http://www.example.com/someuri')
        )
    client.publish(nanopub)
