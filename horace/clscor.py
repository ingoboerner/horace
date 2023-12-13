"""
CLSCor
Additional functionality for CLS INFRA/CLSCor integration of POSTDATA Resources
"""

from rdflib import Graph, URIRef, RDF, RDFS, Literal
import hashlib
from core import CRM, LRM, CORE, CLS, DIG, FABIO

def shorthash(textstring: str, chars: int = 10) -> str:
    """Create a trunctaded sha256 hash of a string

    Args:
        textstring: Text to produce a shorthash from.
        chars (int): length of shorted hash. Defaults to 10.

    Returns:
        str: shorted sha256 hash
    """
    hashed = hashlib.sha256(textstring.encode("UTF-8")).hexdigest()
    shorthash = hashed[:chars]
    return shorthash


def generate_uri(identifier: str, base:str = "https://clscor.io/entity", type:str = None) -> str:
    """Generate a URI. Will hash the idententifier to desematisize
    """
    hash = shorthash(identifier)
    if type is not None:
        uri = f"{base}/{type}/{hash}"
    else:
        uri = f"{base}/{hash}"
    return uri


# URIs of various skos:Concepts/ crm:E55_Types that are used in CLSCor
E55_TYPE_URIS = dict(
  wikidata="https://clscor.io/entity/type/identifier/wikidata",
  viaf="https://clscor.io/entity/type/identifier/viaf",
  bibl_ref="https://clscor.io/entity/type/identifier/bibl_ref",
  print_publication="https://clscor.io/entity/type/publication/print",
  digital_publication="https://clscor.io/entity/type/publication/digital",
  tei_xml="https://clscor.io/entity/type/format/tei",
  json="https://clscor.io/entity/type/format/json",
  digital_source_doc="https://clscor.io/entity/type/document_source/digital",
  download_link="https://clscor.io/entity/type/link/download",
  full_title="https://clscor.io/entity/type/appellation/full_title"
)

CLSCOR_POSTDATA_TYPE_URIS = dict(
  work_conception_date=generate_uri("postdata/type/work_conception_date"),
  work_title=generate_uri("postdata/type/poem_title"),
  actor_name=generate_uri("postdata/type/actor_name"),
  poem_alt_title=generate_uri("postdata/type/poem_alt_title"),
  corpus_slug=generate_uri("postdata/type/corpus_slug"),
  corpus_data_dump=generate_uri("postdata/type/corpus_data_dump")
)


# Corpora that can be downloaded with averell are here: (IB)
    # https://github.com/linhd-postdata/averell-docker/blob/main/src/averell/corpora.yaml

    # disco2_1: Disco V2.1, https://github.com/pruizf/disco/archive/v2.1.zip
    # disco3: Disco V3, https://github.com/pruizf/disco/archive/v3.zip
    # adso: Sonetos Siglo de Oro, https://github.com/bncolorado/CorpusSonetosSigloDeOro/archive/master.zip
    # adso 100: ADSO 100 poems corpus, https://github.com/linhd-postdata/adsoScansionSystem/releases/download/1.0.0/ADSO_gold_standard_100poems.zip
    # plc: Poesía Lírica Castellana Siglo de Oro, https://github.com/bncolorado/CorpusGeneralPoesiaLiricaCastellanaDelSigloDeOro/archive/master.zip
    # gongo: Gongocorpus, https://github.com/linhd-postdata/gongocorpus/archive/master.zip
    # fbfv: [This is not in the averell list!]
    # ecpa: Eighteenth Century Poetry Archive, https://github.com/alhuber1502/ECPA/archive/master.zip

    # Don't know what fbfv is, need to check if it gets loaded at all... (IB)

# took the metadata from the averell repo and included it here (IB)

corpus_metadata = {
  "disco2_1": {
    "name": "Disco V2.1",
    "properties": {
      "slug": "disco2_1",
      "license": "CC-BY",
      "language": "es",
      "reader": "averell.readers.disco",
      "url": "https://github.com/pruizf/disco/archive/v2.1.zip",
      "size": "22M",
      "doc_quantity": 4088,
      "word_quantity": 381539,
      "granularity": [
        "stanza",
        "line"
      ]
    }
  },
  "disco3": {
    "name": "Disco V3",
    "properties": {
      "slug": "disco3",
      "license": "CC-BY",
      "language": "es",
      "reader": "averell.readers.disco3",
      "url": "https://github.com/pruizf/disco/archive/v3.zip",
      "size": "28M",
      "doc_quantity": 4080,
      "word_quantity": 377978,
      "granularity": [
        "stanza",
        "line"
      ]
    }
  },
  "adso": {
    "name": "Sonetos Siglo de Oro",
    "properties": {
      "slug": "adso",
      "license": "CC-BY-NC 4.0",
      "language": "es",
      "reader": "averell.readers.sdo",
      "url": "https://github.com/bncolorado/CorpusSonetosSigloDeOro/archive/master.zip",
      "size": "6.8M",
      "doc_quantity": 5078,
      "word_quantity": 466012,
      "granularity": [
        "stanza",
        "line"
      ]
    }
  },
  "adso100": {
    "name": "ADSO 100 poems corpus",
    "properties": {
      "slug": "adso100",
      "license": "CC-BY-NC 4.0",
      "language": "es",
      "reader": "averell.readers.sdo",
      "url": "https://github.com/linhd-postdata/adsoScansionSystem/releases/download/1.0.0/ADSO_gold_standard_100poems.zip",
      "size": "128K",
      "doc_quantity": 100,
      "word_quantity": 9208,
      "granularity": [
        "stanza",
        "line"
      ]
    }
  },
  "plc": {
    "name": "Poesía Lírica Castellana Siglo de Oro",
    "properties": {
      "slug": "plc",
      "license": "CC-BY-NC 4.0",
      "language": "es",
      "reader": "averell.readers.plsdo",
      "url": "https://github.com/bncolorado/CorpusGeneralPoesiaLiricaCastellanaDelSigloDeOro/archive/master.zip",
      "size": "3.8M",
      "doc_quantity": 475,
      "word_quantity": 299402,
      "granularity": [
        "stanza",
        "line",
        "word",
        "syllable"
      ]
    }
  },
  "gongo": {
    "name": "Gongocorpus",
    "properties": {
      "slug": "gongo",
      "license": "CC-BY-NC-ND 3.0 FR",
      "language": "es",
      "reader": "averell.readers.gongocorpus",
      "url": "https://github.com/linhd-postdata/gongocorpus/archive/master.zip",
      "size": "9.2M",
      "doc_quantity": 481,
      "word_quantity": 99079,
      "granularity": [
        "stanza",
        "line",
        "word",
        "syllable"
      ]
    }
  },
  "ecpa": {
    "name": "Eighteenth Century Poetry Archive",
    "properties": {
      "slug": "ecpa",
      "license": "CC BY-SA 4.0",
      "language": "en",
      "reader": "averell.readers.ecpa",
      "url": "https://github.com/alhuber1502/ECPA/archive/master.zip",
      "size": "2400M",
      "doc_quantity": 3084,
      "word_quantity": 2063668,
      "granularity": [
        "stanza",
        "line",
        "word"
      ]
    }
  },
  "4b4v": {
    "name": "For Better For Verse",
    "properties": {
      "slug": "4b4v",
      "license": "Unknown",
      "language": "en",
      "reader": "averell.readers.forbetter4verse",
      "url": "https://github.com/waynegraham/for_better_for_verse/archive/master.zip",
      "size": "39.5M",
      "doc_quantity": 103,
      "word_quantity": 41749,
      "granularity": [
        "stanza",
        "line"
      ]
    }
  },
  "mel": {
    "name": "Métrique en Ligne",
    "properties": {
      "slug": "mel",
      "license": "Unknown",
      "language": "fr",
      "reader": "averell.readers.metriqueenligne",
      "url": "https://github.com/linhd-postdata/metrique-en-ligne/archive/master.zip",
      "size": "183M",
      "doc_quantity": 5081,
      "word_quantity": 1850222,
      "granularity": [
        "stanza",
        "line"
      ]
    }
  },
  "bibit": {
    "name": "Biblioteca Italiana",
    "properties": {
      "slug": "bibit",
      "license": "Unknown",
      "language": "it",
      "reader": "averell.readers.bibliotecaitaliana",
      "url": "https://github.com/linhd-postdata/biblioteca_italiana/archive/master.zip",
      "size": "242M",
      "doc_quantity": 25341,
      "word_quantity": 7121246,
      "granularity": [
        "stanza",
        "line",
        "word"
      ]
    }
  },
  "czverse": {
    "name": "Corpus of Czech Verse",
    "properties": {
      "slug": "czverse",
      "license": "CC-BY-SA",
      "language": "cs",
      "reader": "averell.readers.czechverse",
      "url": "https://github.com/versotym/corpusCzechVerse/archive/refs/heads/master.zip",
      "size": "4100M",
      "doc_quantity": 66428,
      "word_quantity": 12636867,
      "granularity": [
        "stanza",
        "line",
        "word"
      ]
    }
  },
  "stichopt": {
    "name": "Stichotheque Portuguese",
    "properties": {
      "slug": "stichopt",
      "license": "Unkwown",
      "language": "pt",
      "reader": "averell.readers.stichotheque",
      "url": "https://gitlab.com/stichotheque/stichotheque-pt/-/archive/master/stichotheque-pt-master.zip",
      "size": "11.8M",
      "doc_quantity": 1702,
      "word_quantity": 168411,
      "granularity": [
        "stanza",
        "line"
      ]
    }
  }
}


def generate_corpus_rdf(corpus_id, out_folder="out"):
    """Generate RDF data for a single corpus identified by its corpus ID; function returns the URI of the corpus
    The function will be called by the generate function in the main module to provide a means of creating a
    corpus rdf file when the data is transformed to rdf
    rdf_root is passed by the generate function
    """
    # get corpus metadata
    cdata = corpus_metadata[corpus_id]
    g = Graph()
    g.bind("crm", CRM)
    g.bind("lrm", LRM)
    g.bind("pdc", CORE)
    g.bind("dig", DIG)
    g.bind("cls", CLS)
    g.bind("fabio", FABIO)
    
    corpus_uri = generate_uri(f"postdata/corpus/{corpus_id}")
    corpus = URIRef(corpus_uri)
    g.add((corpus, RDF.type, CLS.X1_Corpus))
    g.add((corpus, RDFS.label, Literal(f"{cdata['name']} [Corpus; Data downloaded with Averell]")))

    corpus_work_uri = generate_uri(f"postdata/corpus/{corpus_id}/work")
    corpus_work = URIRef(corpus_work_uri)
    g.add((corpus_work, RDF.type, LRM.F1_Work))
    g.add((corpus_work, RDFS.label, Literal(f"{cdata['name']} [Corpus Work]")))

    # Connect corpus Work and corpus (data) using the fabio shortcut
    #URIRef("http://purl.org/spar/fabio/hasManifestation")
    g.add((corpus_work, FABIO.hasManifestation, corpus))
    g.add((corpus, FABIO.isManifestationOf, corpus_work))

    # Add Title (maybe to work and manifestation)
    # field "name"
    corpus_title = URIRef(generate_uri(f"postdata/corpus/{corpus_id}/corpus_title"))
    g.add((corpus_title, RDF.type, CRM.E35_Title))
    g.add((corpus_title, RDFS.label, Literal(f"{cdata['name']} [Corpus Title]")))
    g.add((corpus_title, CRM.P2_has_type, URIRef(E55_TYPE_URIS['full_title'])))
    g.add((URIRef(E55_TYPE_URIS['full_title']), CRM.P2i_is_type_of, corpus_title))
    g.add((corpus_title, CRM.P1i_identifies, corpus_work))
    g.add((corpus_work, CRM.P102_has_title, corpus_title))
    g.add((corpus_title, CRM.P102i_is_title_of, corpus))
    g.add((corpus, CRM.P1_is_identified_by, corpus_title))
    g.add((corpus_title, CRM.P190_has_symbolic_content, Literal(cdata['name'])))

    # "slug"
    corpus_slug = URIRef(generate_uri(f"postdata/corpus/{corpus_id}/corpus_slug"))
    g.add((corpus_slug, RDF.type, CRM.E42_Identifier))
    g.add((corpus_slug, RDFS.label, Literal(f"{cdata['name']} [Corpus Slug]")))
    g.add((corpus_slug, CRM.P2_has_type, URIRef(CLSCOR_POSTDATA_TYPE_URIS['corpus_slug'])))
    g.add((URIRef(CLSCOR_POSTDATA_TYPE_URIS['corpus_slug']), CRM.P2i_is_type_of, corpus_slug))
    g.add((corpus_slug, CRM.P1i_identifies, corpus_work))
    g.add((corpus_work, CRM.P1_is_identified_by, corpus_slug))
    g.add((corpus_slug, CRM.P1i_identifies, corpus))
    g.add((corpus, CRM.P1_is_identified_by, corpus_slug))
    g.add((corpus_slug, CRM.P190_has_symbolic_content, Literal(cdata['properties']['slug'])))

    # There are POSTDATA repositories in the field "url", but also other Git(Hub) repos; this seems to be the "source"
    # "url": "https://gitlab.com/stichotheque/stichotheque-pt/-/archive/master/stichotheque-pt-master.zip",
    corpus_dump = URIRef(generate_uri(f"postdata/corpus/{corpus_id}/data_dump"))
    # g.add((corpus_dump, RDF.type, CLS.X1_Corpus)) # Not sure if this would qualify as a CLSCor Corpus and if we want to have that listed, so I opt for F3 and D1
    g.add((corpus_dump, RDF.type, LRM.F3_Manifestation))
    g.add((corpus_dump, RDF.type, DIG.D1_Digital_Object))
    g.add((corpus_dump, RDFS.label, Literal(f"{cdata['name']} [(Source?) Corpus Data Dump]")))
    g.add((corpus_work, FABIO.hasManifestation, corpus_dump))
    g.add((corpus_dump, FABIO.isManifestationOf, corpus_work))
    g.add((corpus_dump, CRM.P2_has_type, URIRef(CLSCOR_POSTDATA_TYPE_URIS["corpus_data_dump"])))
    g.add((URIRef(CLSCOR_POSTDATA_TYPE_URIS["corpus_data_dump"]), CRM.P2_is_type_of, corpus_dump))

    corpus_dump_url = URIRef(generate_uri(f"postdata/corpus/{corpus_id}/data_dump/url"))
    g.add((corpus_dump_url, RDF.type, CRM.E42_Identifier))
    g.add((corpus_dump_url, RDFS.label, Literal(f"{cdata['name']} [URL of the Corpus Data Dump]")))
    g.add((corpus_dump_url, CRM.P2_has_type, URIRef(E55_TYPE_URIS["download_link"])))
    g.add((corpus_dump_url, CRM.P190_has_symbolic_content, Literal(cdata['properties']['url'])))
    g.add((corpus_dump_url, CRM.P1i_identifies, corpus_dump))
    g.add((corpus_dump, CRM.P1_is_identified_by, corpus_dump_url))


    # store
    file_path = out_folder + "/" + "corpus_" + corpus_id.replace(".", "-") + ".ttl"
    g.serialize(format="ttl", destination=file_path, encoding="utf-8")

    return corpus_uri
