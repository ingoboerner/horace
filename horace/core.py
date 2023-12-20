"""Core module."""
import os
import json
from rdflib import Graph, Namespace, RDF, Literal, XSD, RDFS, OWL
from utils import create_uri, NAMESPACES, URIRef, slugify
import requests

CORE = Namespace("http://postdata.linhd.uned.es/ontology/postdata-core#")
KOS = Namespace("http://postdata.linhd.uned.es/kos/")
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
LRM = Namespace("http://iflastandards.info/ns/lrm/lrmoo/")
CLS = Namespace("https://clscor.io/ontologies/CRMcls/")
DIG = Namespace("http://www.ics.forth.gr/isl/CRMdig/")
FABIO = Namespace("http://purl.org/spar/fabio/")

import logging

from clscor import generate_uri as generate_clscor_uri, E55_TYPE_URIS, CLSCOR_POSTDATA_TYPE_URIS

def to_rdf(_json) -> Graph:
    graph = add_core_elements(_json)
    return graph


def add_core_elements(cj_store, _json, name):
    graph = Graph(store=cj_store, identifier="tag:stardog:api:context:default")

    # Add namespaces
    for prefix, uri_ns in NAMESPACES.items():
        graph.namespace_manager.bind(prefix, uri_ns)

    # Get mandatory keys
    poem_title = _json["poem_title"]
    author = _json["author"]
    dataset = _json["corpus"]

    # Creation of mandatory resources
    # These are the official POSTDATA URIs
    # will create pd:p_cervantes = http://postdata.linhd.uned.es/resource/p_cervantes
    # in CLSCor these will only be owl:sameAs; we keep them for possible compability reasons
    # the following part is ugly

    # For CLSCor we add rdfs:labels including author and title
    clscor_short_title = f"{author}: {poem_title}"

    legacy_r_redaction = create_uri("R", author, poem_title, dataset) # POSTDATA Legacy URI
    r_redaction = URIRef(generate_clscor_uri(str(legacy_r_redaction)))
    graph.add((r_redaction, OWL.sameAs, legacy_r_redaction))
    graph.add((legacy_r_redaction, OWL.sameAs, r_redaction))
    graph.add((r_redaction, RDFS.label, Literal(f"{clscor_short_title} [Expression]"))) # rdfs:label for CLSCor

    
    legacy_r_agent_role = create_uri("AR", author, poem_title) # POSTDATA Legacy URI
    r_agent_role = URIRef(generate_clscor_uri(str(legacy_r_agent_role)))
    graph.add((r_agent_role, OWL.sameAs, legacy_r_agent_role))
    graph.add((legacy_r_agent_role, OWL.sameAs, r_agent_role))
    graph.add((r_agent_role, RDFS.label, Literal(f"{clscor_short_title} [Agent Role]"))) # rdfs:label for CLSCor
    
    legacy_r_poetic_work = create_uri("PW", author, poem_title) # POSTDATA Legacy URI
    r_poetic_work = URIRef(generate_clscor_uri(str(legacy_r_poetic_work)))
    graph.add((legacy_r_poetic_work, OWL.sameAs, r_poetic_work))
    graph.add((r_poetic_work, OWL.sameAs, legacy_r_poetic_work))
    graph.add((r_poetic_work, RDFS.label, Literal(f"{clscor_short_title} [Work]"))) # rdfs:label for CLSCor
    
    legacy_r_person = create_uri("P", author) # POSTDATA Legacy URI
    r_person = URIRef(generate_clscor_uri(str(legacy_r_person)))
    graph.add((legacy_r_person, OWL.sameAs, r_person))
    graph.add((r_person, OWL.sameAs, legacy_r_person))
    graph.add((r_person, RDFS.label, Literal(f"{author} [Actor]"))) # rdfs:label for CLSCor
    
    legacy_r_work_conception = create_uri("WC", author, poem_title) # POSTDATA Legacy URI
    r_work_conception = URIRef(generate_clscor_uri(str(legacy_r_work_conception)))
    graph.add((legacy_r_work_conception, OWL.sameAs, r_work_conception))
    graph.add((r_work_conception, OWL.sameAs, legacy_r_work_conception))
    graph.add((r_work_conception, RDFS.label, Literal(f"{clscor_short_title} [Creation of Work]"))) # rdfs:label for CLSCor

    # These are needed additionally for CLSCor:
    # There are no owl:sameAs stmts because these entities are not covered by POSTDATA / there are no equivalents in the Core Ontology 
    r_work_title_node = URIRef(generate_clscor_uri(str(create_uri("NEW_WT", author, poem_title)))) # WIll be the title of the F1 and the F2!
    graph.add((r_work_title_node, RDFS.label, Literal(f"{clscor_short_title} [Title]"))) # rdfs:label for CLSCor      
    
    r_author_name_node = URIRef(generate_clscor_uri(str(create_uri("NEW_AN", author))))
    graph.add((r_author_name_node, RDFS.label, Literal(f"{author} [Name of Actor]"))) # rdfs:label for CLSCor

    r_expression_creation = create_uri("F2CREATION", author, poem_title)
    graph.add((r_expression_creation, RDFS.label, Literal(f"{clscor_short_title} [Creation of Expression]")))

    
    # The actual digital files produced/basis of POSTDATA system are not covered by the POSTDATA, we add them:
    r_corpus_document_averell_tei = URIRef(generate_clscor_uri(str(create_uri("NEW_F3_averell_tei", author, poem_title))))
    graph.add((r_corpus_document_averell_tei, RDFS.label, Literal(f"{clscor_short_title} [TEI File]")))

    r_corpus_document_averell_json = URIRef(generate_clscor_uri(str(create_uri("NEW_F3_averell_json", author, poem_title))))
    graph.add((r_corpus_document_averell_json, RDFS.label, Literal(f"{clscor_short_title} [JSON File]")))

    # There is (probably) an original file – the digital source in the source corpora. We don't know much about it, but we add it anyway
    r_digital_source_document = URIRef(generate_clscor_uri(str(create_uri("NEW_F3_digital_source_file", author, poem_title))))
    graph.add((r_digital_source_document, RDFS.label, Literal(f"{clscor_short_title} [Digital Source Document]")))

    # Assignation of types for mandatory resources

    # Mapping: pdc:PoeticWork owl:subClassOf lrm:F1_Work; we add both classes here
    graph.add((r_poetic_work, RDF.type, CORE.PoeticWork)) #Legacy POSTDATA
    graph.add((r_poetic_work, RDF.type, LRM.F1_Work)) #CLSCor 

    # It is still not decided of the pdc:Redaction can be a Manfestation; in the pdc Redaction is an equivalent to frbr: Self-Contained Expression (have not checked!)
    graph.add((r_redaction, RDF.type, CORE.Redaction)) #Legacy POSTDATA
    graph.add((r_redaction, RDF.type, LRM.F2_Expression)) #CLSCore

    # The "Digital File" / X2 Corpus Document, i.e. the F3 Manifestation is not foreseen in the POSTDATA modeling; we add it
    # There is at least the unified JSON file that is downloaded by Averell
    graph.add((r_corpus_document_averell_json, RDF.type, CLS.X2_Corpus_Document))
    graph.add((r_corpus_document_averell_json, CLS.Y2_has_format, URIRef(E55_TYPE_URIS["json"]))) # in CLSCor we add format (and schema)
    graph.add((URIRef(E55_TYPE_URIS["json"]), CLS.Y2i_is_format_of, r_corpus_document_averell_json))
    # TODO: and Schema (Averell JSON)

    # in theory, the new averell produces TEI as well; we can foresee that file as well
    graph.add((r_corpus_document_averell_tei, RDF.type, CLS.X2_Corpus_Document))
    graph.add((r_corpus_document_averell_tei, CLS.Y2_has_format, URIRef(E55_TYPE_URIS["tei_xml"]))) # in CLSCor we add format (and schema)
    graph.add((URIRef(E55_TYPE_URIS["tei_xml"]), CLS.Y2i_is_format_of, r_corpus_document_averell_tei))
    # TODO: add Averell-TEI Schema (this is far less developed than the JSON)
    # TODO: maybe identify this file on GitHub

    # There is also a digital Source File (That is part of the source corpus and has been transformed to the uniform Averell JSON)
    # This is NOT part of the POSTDATA Corpus, but of a different corpus; we don't know anything about the format at the moment
    graph.add((r_digital_source_document, RDF.type, CLS.X2_Corpus_Document))
    # Here we don't know format or schema. Maybe could be related to the Corpus Table at some point

    # Connect an Agent to the creation:
    # POSTDATA uses a reification of the crm: Property P14_carried_out_by; but a specialized version
    graph.add((r_agent_role, RDF.type, CORE.AgentRole)) #POSTDATA legacy
    graph.add((r_agent_role, RDF.type, CRM.PC14_carried_out_by)) # more generic CLSCor /CIDOC

    # Person involved in creating the Work
    graph.add((r_person, RDF.type, CORE.Person)) # POSTDATA
    graph.add((r_person, RDF.type, CRM.E39_Actor)) # maybe map to E39_Actor; could also use crm:E21_Person Generic CLSCor
    
    # Creating of the Work
    graph.add((r_work_conception, RDF.type, CORE.WorkConception)) # POSTDATA
    graph.add((r_work_conception, RDF.type, LRM.F27_Work_Creation)) # Generic LRMoo for CLSCor

    # CLSCor specific: Creating the Expression
    graph.add((r_expression_creation, RDF.type, LRM.F28_Expression_Creation))

    # Data Properties for mandatory resources
    
    # Title of a Poem
    graph.add((r_poetic_work, CORE.title, Literal(poem_title))) # POSTDATA included the title as a owl:dataTypeProperty; this actually a shortcut is expanded below
    # CLS Cor/CIDOC/LRMoo (Work)
    graph.add((r_poetic_work, CRM.P102_has_title, r_work_title_node))
    graph.add((r_work_title_node, CRM.P102i_is_title_of, r_poetic_work))
    graph.add((r_work_title_node, RDF.type, CRM.E35_Title))
    graph.add((r_work_title_node, CRM.P190_has_symbolic_content, Literal(poem_title)))
    graph.add((r_work_title_node, CRM.P2_has_type, URIRef(CLSCOR_POSTDATA_TYPE_URIS['poem_title']))) # Type of Title specific to POSTDATA data
    graph.add((URIRef(CLSCOR_POSTDATA_TYPE_URIS['poem_title']), CRM.P2i_is_type_of, r_work_title_node))

    # Also add the title to the expression f2 as well
    graph.add((r_redaction, CRM.P102_has_title, r_work_title_node))
    graph.add((r_work_title_node, CRM.P102i_is_title_of, r_redaction))

    # Author name
    graph.add((r_person, CORE.name, Literal(author))) # this is a shortcut introduced by POSTDATA for the construct below
    
    # CLSCor /CIDOC /LRMoo
    graph.add((r_author_name_node, RDF.type, CRM.E41_Appellation))
    graph.add((r_author_name_node, CRM.P190_has_symbolic_content, Literal(author)))
    graph.add((r_person, CRM.P1_is_identified_by, r_author_name_node))
    graph.add((r_author_name_node, CRM.P2_has_type, URIRef(CLSCOR_POSTDATA_TYPE_URIS['actor_name'])))
    graph.add((URIRef(CLSCOR_POSTDATA_TYPE_URIS['actor_name']), CRM.P2i_is_type_of, r_author_name_node))
     

    # Object Properties for mandatory resources
    
    # Connect Work and Expression
    # POSTDATA:
    graph.add((r_poetic_work, CORE.isRealisedThrough, r_redaction))
    graph.add((r_redaction, CORE.realises, r_poetic_work))
    # CLSCor
    graph.add((r_poetic_work, LRM.R3_is_realised_in, r_redaction))
    graph.add((r_redaction, LRM.R3i_realises, r_poetic_work))

    # Creation of a Work
    graph.add((r_work_conception, CORE.initiated, r_poetic_work))
    graph.add((r_poetic_work, CORE.wasInitiatedBy, r_work_conception))
    # LRMoo:
    graph.add((r_work_conception, LRM.R16_created, r_poetic_work))
    graph.add((r_poetic_work, LRM.R16i_was_created_by, r_work_conception))

    # Creation of Expression
    graph.add((r_expression_creation, LRM.R17_created, r_redaction))
    graph.add((r_redaction, LRM.R17i_was_created_by, r_expression_creation))

    # Connect the author
    # POSTDATA:
    graph.add((r_work_conception, CORE.hasAgentRole, r_agent_role))
    graph.add((r_agent_role, CORE.isAgentRoleOf, r_work_conception))
    # CLSCor
    graph.add((r_work_conception, CRM.P01i_is_domain_of, r_agent_role))
    graph.add((r_agent_role, CRM.P01_has_domain, r_work_conception))

    # POSTDATA:
    graph.add((r_agent_role, CORE.hasAgent, r_person))
    graph.add((r_person, CORE.isAgentOf, r_agent_role))
    # CLSCor
    graph.add((r_agent_role, CRM.P02_has_range, r_person))
    graph.add((r_person, CRM.P02i_is_range_of, r_agent_role))

    graph.add((r_agent_role, CORE.roleFunction, KOS.Creator)) # POSTDATA
    graph.add((r_agent_role, CRM["P14.1_in_the_role_of"], KOS.Creator)) # CLSCor
    graph.add((KOS.Creator, RDFS.label, Literal("Creator", lang="en")))

    # CLSCor connect the author to the Expression Creation without reification (hope this works!)
    graph.add((r_expression_creation, CRM.P14_carried_out_by, r_person))
    graph.add((r_person, CRM.P14i_performed, r_expression_creation))

    # Key for year : year
    # Add year of poetic work conception
    # POSTDATA records a "Work Conception Date". In CLSCor this could be a E55 Type and be attached to the Time-Span
    if "year" in _json.keys():
        work_date = _json["year"]
        if work_date is not None:
            legacy_r_conception_date = create_uri("TS_C_", author, poem_title)
            r_conception_date = URIRef(generate_clscor_uri(str(legacy_r_conception_date)))
            graph.add(
                (r_conception_date, RDF.type, CORE.TimeSpan),
                (r_conception_date, RDF.type, CRM["E52_Time-Span"]),
                (r_conception_date, RDFS.label, Literal(f"{clscor_short_title} [Work Conception Date]")),
                (r_conception_date, CLS.P2_has_type, URIRef(CLSCOR_POSTDATA_TYPE_URIS["work_conception_date"])),
                (r_conception_date, OWL.sameAs, legacy_r_conception_date),
                (legacy_r_conception_date, OWL.sameAs, r_conception_date)
                )
            if work_date.isdigit():
                # Distinguish DPs or distinguish classes (date, textualDate VS period, timePoint)
                graph.add((r_conception_date, CORE.date, Literal(work_date, datatype=XSD.date)))
            else:
                graph.add((r_conception_date, CORE.date, Literal(work_date, datatype=XSD.string)))

            graph.add((r_work_conception, CORE.hasTimeSpan, r_conception_date)) # POSTDATA 
            graph.add((r_conception_date, CORE.isTimeSpanOf, r_work_conception)) #POSTDATA

            graph.add((r_work_conception, CRM["P4_has_time-span"], r_conception_date)) # CLSCor 
            graph.add((r_conception_date, CRM["P4i_is_time-span_of"], r_work_conception)) #CLSCor


    # Key for alt title : poem_alt_title
    # Add alternative poetic work title
    if "poem_alt_title" in _json.keys():
        alt_title = _json["poem_alt_title"]
        # graph.add((r_poetic_work, CORE.alternativeTitle, Literal(alt_title, lang="es")))
        r_work_alt_title_node = create_uri("NEW_AT", author, poem_title)
        graph.add((r_work_alt_title_node, RDF.type, CRM.E35_Title))
        graph.add((r_work_alt_title_node, CRM.P190_has_symbolic_content, Literal(alt_title, lang="es")))
        graph.add((r_poetic_work, CRM.P1_is_identified_by, r_work_alt_title_node))
        graph.add((r_work_alt_title_node ,CRM.P2_has_type, URIRef(CLSCOR_POSTDATA_TYPE_URIS["poem_alt_title"])))
        graph.add((URIRef(CLSCOR_POSTDATA_TYPE_URIS["poem_alt_title"]), CRM.P2i_is_type_of, r_work_alt_title_node))


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

    # CLSCor specific from here on

    # Connect the individual file to the corpus
    graph.add((r_corpus_document_averell_json, LRM.R71i_is_part_of, URIRef(generate_clscor_uri(f"postdata/corpus/{dataset}"))))
    graph.add((URIRef(generate_clscor_uri(f"postdata/corpus/{dataset}")), LRM.R71_has_part, r_corpus_document_averell_json))
    # The TEI version of the Averell File will float around for now

    # Connect the Work to the Corpus Work
    # corpus_work_uri = generate_uri(f"postdata/corpus/{dataset}/work")
    graph.add((r_poetic_work, LRM.R67i_forms_part_of, URIRef(generate_clscor_uri(f"postdata/corpus/{dataset}/work"))))
    graph.add((URIRef(generate_clscor_uri(f"postdata/corpus/{dataset}/work")), LRM.R67_has_part, r_poetic_work))

    # Connect Expression and manifestations (CLSCor only)
    # Manifestation embodies Expression
    graph.add((r_redaction, LRM.R4i_is_embodied_in, r_corpus_document_averell_json))
    graph.add((r_corpus_document_averell_json, LRM.R4_embodies, r_redaction)) 

    graph.add((r_redaction, LRM.R4i_is_embodied_in, r_corpus_document_averell_tei))
    graph.add((r_corpus_document_averell_tei, LRM.R4_embodies, r_redaction))

    graph.add((r_redaction, LRM.R4i_is_embodied_in, r_digital_source_document))
    graph.add((r_digital_source_document, LRM.R4_embodies, r_redaction))

    # Raw Link of the files (experimental)
    # Averall Docker includes the files (I think): 
    # e.g. https://raw.githubusercontent.com/linhd-postdata/averell-docker/main/corpora/JSON/adso100/averell/parser/cervantes/amadis-de-gaula-a-don-quijote.json
    # https://raw.githubusercontent.com/linhd-postdata/averell-docker/main/corpora/JSON/adso100/averell/parser/Cervantes/Amadís de Gaula a don Quijote de La Mancha.json

    logging.debug(f"File name: {name}")
    #json_raw_url = f"https://raw.githubusercontent.com/linhd-postdata/averell-docker/main/corpora/JSON/{dataset}/averell/parser/{slugify(author)}/{slugify(poem_title)}.json"
    json_raw_url = f"https://raw.githubusercontent.com/linhd-postdata/averell-docker/main/corpora/JSON/{dataset}/averell/parser/{slugify(author)}/{name}.json"
    # maybe name is the better option; this fixes the problem, that the file name in adso100 (at least) is not equal to the title
    # In theory this should work for the TEI files as well, but in this case the folder/file structure on github is different, e.g. "Cervantes" instead of "cervantes" ...
    # could use request and check for status code 200 (will slow down processing) Would need to change the CHECK_RAW_URL to True

    CHECK_RAW_URL = False
    # Checking was nice but it slows down, so I don't do it. it worked for all adso100 files. If I test another corpus, might become handy to verify the links later

    if CHECK_RAW_URL == True:
        r = requests.get(json_raw_url)
        if r.status_code == 200:

            averell_json_rawlink = URIRef(generate_clscor_uri(create_uri("JSON_RAW", author, poem_title)))
            graph.add((averell_json_rawlink, RDF.type, CRM.E42_Identifier))
            graph.add((averell_json_rawlink, RDFS.label, Literal(f"{clscor_short_title} [Link to JSON File]")))
            graph.add((averell_json_rawlink, CRM.P190_has_symbolic_content, Literal(json_raw_url)))
            graph.add((averell_json_rawlink, CRM.P1i_identifies, r_corpus_document_averell_json))
            graph.add((r_corpus_document_averell_json, CRM.P1_is_identified_by, averell_json_rawlink))
            graph.add((averell_json_rawlink, CRM.P2_has_type, URIRef(E55_TYPE_URIS['download_link'])))
            graph.add((URIRef(E55_TYPE_URIS['download_link']), CRM.P2i_is_type_of, averell_json_rawlink))
        elif r.status_code == 404:
            #print("Can't generate Rawlink.")
            logging.warning(f"Can't generate Rawlink fo {dataset}, {author}, {poem_title}")
        else:
            raise Exception(r.status_code)
    else:
        # Do not check if the link resolves at all
        averell_json_rawlink = URIRef(generate_clscor_uri(create_uri("JSON_RAW", author, poem_title)))
        graph.add((averell_json_rawlink, RDF.type, CRM.E42_Identifier))
        graph.add((averell_json_rawlink, RDFS.label, Literal(f"{clscor_short_title} [Link to JSON File]")))
        graph.add((averell_json_rawlink, CRM.P190_has_symbolic_content, Literal(json_raw_url)))
        graph.add((averell_json_rawlink, CRM.P1i_identifies, r_corpus_document_averell_json))
        graph.add((r_corpus_document_averell_json, CRM.P1_is_identified_by, averell_json_rawlink))
        graph.add((averell_json_rawlink, CRM.P2_has_type, URIRef(E55_TYPE_URIS['download_link'])))
        graph.add((URIRef(E55_TYPE_URIS['download_link']), CRM.P2i_is_type_of, averell_json_rawlink))

