"""Core module."""
import os
import json
from rdflib import Graph, Namespace, RDF, Literal, XSD, RDFS
from utils import create_uri, NAMESPACES, URIRef, slugify


CORE = Namespace("http://postdata.linhd.uned.es/ontology/postdata-core#")
KOS = Namespace("http://postdata.linhd.uned.es/kos/")
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
LRM = Namespace("http://iflastandards.info/ns/lrm/lrmoo/")
CLS = Namespace("https://clscor.io/ontologies/CRMcls/")
DIG = Namespace("http://www.ics.forth.gr/isl/CRMdig/")


def to_rdf(_json) -> Graph:
    graph = add_core_elements(_json)
    return graph


def add_core_elements(cj_store, _json):
    graph = Graph(store=cj_store, identifier="tag:stardog:api:context:default")

    # Add namespaces
    for prefix, uri_ns in NAMESPACES.items():
        graph.namespace_manager.bind(prefix, uri_ns)

    # Get mandatory keys
    poem_title = _json["poem_title"]
    author = _json["author"]
    dataset = _json["corpus"]

    # Creation of mandatory resources
    r_redaction = create_uri("R", author, poem_title, dataset)
    r_agent_role = create_uri("AR", author, poem_title)
    r_poetic_work = create_uri("PW", author, poem_title)
    r_person = create_uri("P", author)
    r_work_conception = create_uri("WC", author, poem_title)

    r_work_title_node = create_uri("NEW_WT", author, poem_title)
    r_author_name_node = create_uri("NEW_AN", author)

    # Assignation of types for mandatory resources
    graph.add((r_poetic_work, RDF.type, LRM.F1_Work))
    graph.add((r_redaction, RDF.type, LRM.F2_Expression))

    graph.add((r_agent_role, RDF.type, CRM.PC14_carried_out_by))

    graph.add((r_person, RDF.type, CRM.E39_Actor)) # maybe map to E39_Actor; could also use crm:E21_Person
    graph.add((r_work_conception, RDF.type, LRM.F27_Work_Creation))

    # Data Properties for mandatory resources
    # graph.add((r_poetic_work, CORE.title, Literal(poem_title))) # this shortcut is expanded below
    graph.add((r_poetic_work, CRM.P102_has_title, r_work_title_node))
    graph.add((r_work_title_node, RDF.type, CRM.E35_Title))
    graph.add((r_work_title_node, CRM.P190_has_symbolic_content, Literal(poem_title)))
    # TODO: still have to add the type of the Title (E55 Type)

    #graph.add((r_person, CORE.name, Literal(author)))
    graph.add((r_author_name_node, RDF.type, CRM.E41_Appellation))
    graph.add((r_author_name_node, CRM.P190_has_symbolic_content, Literal(author)))
    graph.add((r_person, CRM.P1_is_identified_by, r_author_name_node))
    # TODO: still have to add the type of the Title (E55 Type)

    # Object Properties for mandatory resources
    graph.add((r_poetic_work, LRM.R3_is_realised_in, r_redaction))
    graph.add((r_redaction, LRM.R3i_realises, r_poetic_work))

    graph.add((r_work_conception, LRM.R16_created, r_poetic_work))
    graph.add((r_poetic_work, LRM.R16i_was_created_by, r_work_conception))

    graph.add((r_work_conception, CRM.P01i_is_domain_of, r_agent_role))
    graph.add((r_agent_role, CRM.P01_has_domain, r_work_conception))

    graph.add((r_agent_role, CRM.P02_has_range, r_person))
    graph.add((r_person, CRM.P02i_is_range_of, r_agent_role))

    graph.add((r_agent_role, CRM["P14.1_in_the_role_of"], KOS.Creator))
    graph.add((KOS.Creator, RDFS.label, Literal("Creator", lang="en")))

    # Key for year : year
    # Add year of poetic work conception
    # IB: we don't have a good pattern for this at the moment, will have to look into this again.
    if "year" in _json.keys():
        work_date = _json["year"]
        if work_date is not None:
            r_conception_date = create_uri("TS_C_", author, poem_title)
            graph.add(
                (r_conception_date, RDF.type, CORE.TimeSpan))
            if work_date.isdigit():
                # Distinguish DPs or distinguish classes (date, textualDate VS period, timePoint)
                graph.add((r_conception_date, CORE.date, Literal(work_date, datatype=XSD.date)))
            else:
                graph.add((r_conception_date, CORE.date, Literal(work_date, datatype=XSD.string)))

            graph.add((r_work_conception, CORE.hasTimeSpan, r_conception_date))
            graph.add((r_conception_date, CORE.isTimeSpanOf, r_work_conception))

    # Key for alt title : poem_alt_title
    # Add alternative poetic work title
    if "poem_alt_title" in _json.keys():
        alt_title = _json["poem_alt_title"]
        # graph.add((r_poetic_work, CORE.alternativeTitle, Literal(alt_title, lang="es")))
        r_work_alt_title_node = create_uri("NEW_AT", author, poem_title)
        graph.add((r_work_alt_title_node, RDF.type, CRM.E35_Title))
        graph.add((r_work_alt_title_node, CRM.P190_has_symbolic_content, Literal(alt_title, lang="es")))
        graph.add((r_poetic_work, CRM.P1_is_identified_by, r_work_alt_title_node))

    # Key for poem type : structure
    # Add poetic work genre
    if "structure" in _json.keys():
        genre = _json["structure"]
        r_genre = URIRef(KOS + slugify(genre))
        graph.add((r_poetic_work, CORE.genre, r_genre))
        graph.add((r_genre, RDFS.label, Literal(genre)))

    # Add textual content
    if "stanzas" in _json.keys():
        # print("LEN", len([stanza["stanza_text"] for stanza in _json["stanzas"]]))
        text = "\n\n".join(stanza["stanza_text"] for stanza in _json["stanzas"])
        graph.add((r_redaction, CORE.text, Literal(text)))
        # print(text)
    # return conjunctive_graph
