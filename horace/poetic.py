from rantanplan.core import format_stress
from rdflib import Graph, RDF, Namespace, Literal, XSD, URIRef, RDFS

from utils import create_uri, slugify, NAMESPACES
import time

from jollyjumper import get_enjambment

POETIC = Namespace(NAMESPACES["pdp"])
CORE = Namespace("http://postdata.linhd.uned.es/ontology/postdata-core#")
KOS = Namespace("http://postdata.linhd.uned.es/kos/")
SKOS = Namespace(NAMESPACES["skos"])
DIG = Namespace("http://www.ics.forth.gr/isl/CRMdig/")
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
LRM = Namespace("http://iflastandards.info/ns/lrm/lrmoo/")
CLS = Namespace("https://clscor.io/ontologies/CRMcls/")

from clscor import generate_uri as generate_clscor_uri, E55_TYPE_URIS, CLSCOR_POSTDATA_TYPE_URIS


def add_metrical_elements(cj_store, _json, n_doc) -> str:
    # g = Graph()
    poem_title = _json["poem_title"]
    author = _json["author"]
    dataset = _json["corpus"]

    f_time = str(time.time())
    stamp = f_time[0:10] + f_time[11:]

    # In CLSCor there most likely won't be a named graph for the analysis data though
    # I have not removed it yet
    # This is the manual annotation process
    graph_name = "http://postdata.linhd.uned.es/M_" + slugify(author) + "_" + slugify(poem_title) + "_" + str(stamp)
    g = Graph(cj_store, graph_name)
    g_def = Graph(cj_store, "tag:stardog:api:context:default")

    # Redaction resource
    # This is the same as in core. It get's re-created here. I use the strategy as in the core module (IB)
    legacy_r_redaction = create_uri("R", author, poem_title, dataset)
    r_redaction = URIRef(generate_clscor_uri(str(legacy_r_redaction)))
    g_def.add((r_redaction, RDF.type, CORE.Redaction)) # this will be done in the core module for CLSCor

    annotation_author = "UNKNOWN"

    if "stanzas" in _json.keys():
        # Add manual annotation event
        r_event_scansion = create_uri("SP", author, poem_title, dataset, stamp)
        g_def.add((r_event_scansion, RDF.type, POETIC.ScansionProcess))
        # CLSCor: Just for orientation, add a lable that says it is a manual process
        g_def.add((r_event_scansion, RDFS.label, Literal(f"Manual Scansion Process of {author}: {poem_title}")))
        # Add scansion class
        r_scansion = create_uri("SC", author, poem_title, dataset, stamp)
        g_def.add((r_scansion, RDF.type, POETIC.Scansion))
        # Scansion used redaction
        g_def.add((r_event_scansion, POETIC.usedAsInput, r_redaction))
        g_def.add((r_redaction, POETIC.wasInputFor, r_event_scansion))
        # Scansion event generated scansion
        g_def.add((r_event_scansion, POETIC.generated, r_scansion))
        g_def.add((r_scansion, POETIC.isGeneratedBy, r_event_scansion))
        # Type of scansion
        r_concept_manual_scansion = URIRef(KOS + "ManualAnnotation")
        g_def.add((r_scansion, POETIC.typeOfScansion, r_concept_manual_scansion))
        g_def.add((r_concept_manual_scansion, RDFS.label,
               Literal("Manual Annotation")))
        # Add graph information
        # In CLSCor we don't have the graph information. I remove it here (IB)
        # g_def.add((r_scansion, POETIC.graphName, URIRef(graph_name)))

        # SCANSION TO FILE ID
        # if n_doc is not None:
        #     g.add((r_scansion, POETIC.id, Literal("poem_" + str(n_doc) + "_M")))

        # SCANSION TO GRAPH NAME
        # g.add((r_scansion, POETIC.graph, URIRef(graph_name)))

        # Include the agent of the manual annotation
        r_agent_role = create_uri("AR", author, poem_title, dataset, stamp)
        g_def.add((r_event_scansion, CORE.hasAgentRole, r_agent_role))
        g_def.add((r_agent_role, CORE.isAgentRoleOf, r_event_scansion))
        r_agent = create_uri("A", annotation_author)
        g_def.add((r_agent, CORE.isAgentOf, r_agent_role))
        g_def.add((r_agent_role, CORE.hasAgent, r_agent))
        g_def.add((r_agent, CORE.name, Literal(annotation_author)))
        r_role_function = URIRef(KOS + slugify("ManualAnnotator"))
        g_def.add((r_agent_role, CORE.roleFunction, r_role_function))
        g_def.add((r_role_function, RDFS.label, Literal("Manual Annotator")))

        # Add stanza list
        r_stanza_list = create_uri("SL", poem_title, author, dataset, stamp)
        g.add((r_stanza_list, RDF.type, POETIC.StanzaList))
        g.add((r_stanza_list, POETIC.numberOfStanzas, Literal(len(_json["stanzas"]), datatype=XSD.nonNegativeInteger)))

        # Include stanza list to scansion process
        g.add((r_scansion, POETIC.hasListAnnotation, r_stanza_list))
        g.add((r_stanza_list, POETIC.isListAnnotatedBy, r_scansion))

        # Add stanza list to scansion
        g.add((r_scansion, POETIC.hasStanzaList, r_stanza_list))
        g.add((r_stanza_list, POETIC.isStanzaListof, r_scansion))

        n_absolute_lines = 0
        for st_i, stanza in enumerate(_json["stanzas"]):
            stanza_number = str(stanza["stanza_number"])
            stanza_text = stanza["stanza_text"]

            # Create stanza
            r_stanza = create_uri("ST", stanza_number, author, poem_title, dataset, stamp)
            # Add Stanza Type
            g.add((r_stanza, RDF.type, POETIC.Stanza))
            # Add Stanza to stanza list
            g.add((r_stanza_list, POETIC.stanza, r_stanza))
            g.add((r_stanza, POETIC.stanzaList, r_stanza_list))
            # Add Stanza to scansion
            g.add((r_scansion, POETIC.hasStanza, r_stanza))
            g.add((r_stanza, POETIC.isStanzaOf, r_scansion))

            # First, last, next, previous
            if st_i == 0:
                g.add((r_stanza_list, POETIC.firstStanza, r_stanza))
                g.add((r_stanza, POETIC.firstStanzaOf, r_stanza_list))
            elif st_i == len(_json["stanzas"]) - 1:
                g.add((r_stanza_list, POETIC.lastStanza, r_stanza))
                g.add((r_stanza, POETIC.lastStanzaOf, r_stanza_list))
            if st_i < len(_json["stanzas"]) - 2:
                next_st = create_uri("ST", str(st_i + 1), author, poem_title, dataset, stamp)
                g.add((r_stanza, POETIC.nextStanza, next_st))
            if st_i > 0:
                prev_st = create_uri("ST", str(st_i - 1), author, poem_title, dataset, stamp)
                g.add((r_stanza, POETIC.previousStanza, prev_st))

            # Add Stanza DP
            g.add((r_stanza, POETIC.content, Literal(stanza_text)))
            g.add((r_stanza, POETIC.stanzaNumber,
                   Literal(stanza_number, datatype=XSD.nonNegativeInteger)))

            # Check for Stanza type
            # Key for stanza type
            if "stanza_type" in stanza.keys():
                if stanza["stanza_type"] is not None:
                    s_type = stanza["stanza_type"]
                    r_stype = URIRef(KOS + slugify(s_type))
                    g.add((r_stanza, POETIC.typeOfStanza, r_stype))
                    g.add((r_stype, RDFS.label, Literal(s_type)))

            if "lines" in stanza.keys():
                # Create line list
                r_line_list = create_uri("LL", poem_title, author, dataset, str(st_i), stamp)
                # Add LineList type
                g.add((r_line_list, RDF.type, POETIC.LineList))
                g.add((r_line_list, POETIC.numberOfLines, Literal(len(stanza["lines"]), datatype=XSD.nonNegativeInteger)))
                # Add line list to scansion
                g.add((r_scansion, POETIC.hasListAnnotation, r_line_list))
                g.add((r_line_list, POETIC.isListAnnotationOf, r_scansion))

                for l_i, line in enumerate(stanza["lines"]):
                    # line_number = str(line["line_number"])
                    line_text = line["line_text"]

                    r_line = create_uri("L", str(l_i), stanza_number, author, poem_title,
                                          dataset, stamp)
                    # Add line type
                    g.add((r_line, RDF.type, POETIC.Line))
                    # Add line to stanza
                    g.add((r_stanza, POETIC.hasLine, r_line))
                    g.add((r_line, POETIC.isLineOf, r_stanza))
                    # Add line to line list
                    g.add((r_line_list, POETIC.line, r_line))
                    g.add((r_line, POETIC.lineList, r_line_list))

                    if l_i == 0:
                        g.add((r_line_list, POETIC.firstLine, r_line))
                        g.add((r_line, POETIC.firstLineOf, r_line_list))
                    elif l_i == len(stanza["lines"]) - 1:
                        g.add((r_line_list, POETIC.lastLine, r_line))
                        g.add((r_line, POETIC.lastLineOf, r_line_list))
                    if st_i < len(stanza["lines"]) - 2:
                        next_l = create_uri("L", str(l_i + 1), stanza_number, author, poem_title,
                                          dataset, stamp)
                        g.add((r_line, POETIC.nextLine, next_l))
                    if st_i > 0:
                        prev_l = create_uri("L", str(l_i - 1), stanza_number, author, poem_title,
                                          dataset, stamp)
                        g.add((r_line, POETIC.previousLine, prev_l))

                    # Add line DP
                    g.add((r_line, POETIC.content, Literal(line_text)))
                    g.add((r_line, POETIC.relativeLineNumber,
                           Literal(l_i, datatype=XSD.nonNegativeInteger)))
                    g.add((r_line, POETIC.absoluteLineNumber,
                           Literal(n_absolute_lines, datatype=XSD.nonNegativeInteger)))

                    n_absolute_lines += 1

                    if "words" in line.keys():
                        # Create word list
                        r_word_list = create_uri("WL", stanza_number, str(l_i), author, poem_title, dataset, stamp)
                        g.add((r_word_list, RDF.type, POETIC.WordList))
                        g.add((r_word_list, POETIC.numberOfWords, Literal(len(line["words"]), datatype=XSD.nonNegativeInteger)))
                        # Add Word list to line
                        g.add((r_line, POETIC.hasWordList, r_word_list))
                        g.add((r_word_list, POETIC.isWordListOf, r_line))
                        # Add Word List to scansion
                        g.add((r_scansion, POETIC.hasListAnnotation, r_word_list))
                        g.add((r_word_list, POETIC.isListAnnotationOf,
                               r_scansion))

                        count_syllables = 0
                        tot_syllables = None
                        try:
                            all_words = [word for word in line["words"]]
                            all_syllables = [syllable for syllable in all_words]
                            tot_syllables = len(all_syllables)
                        except: pass

                        for w_i, word in enumerate(line["words"]):
                            word_number = str(w_i)
                            word_text = word["word_text"]

                            r_word = create_uri("W", word_number, str(l_i), stanza_number,
                                                  author, poem_title, dataset, stamp)
                            # Add word type
                            g.add((r_word, RDF.type, POETIC.Word))
                            # Add line to word
                            g.add((r_line, POETIC.hasWord, r_word))
                            g.add((r_word, POETIC.isWordOf, r_line))
                            # Add Word DP
                            g.add((r_word, POETIC.content, Literal(word_text)))
                            g.add((r_word, POETIC.wordNumber,
                                   Literal(word_number, datatype=XSD.nonNegativeInteger)))

                            # Add Word to word list
                            g.add((r_word_list, POETIC.word, r_word))
                            g.add((r_word, POETIC.wordList, r_word_list))

                            if w_i == 0:
                                g.add((r_word_list, POETIC.firstWord, r_word))
                                g.add((r_word, POETIC.firstWordOf, r_word_list))
                            elif w_i == len(line["words"]) - 1:
                                g.add((r_word_list, POETIC.lastWord, r_word))
                                g.add((r_word, POETIC.lastWordOf, r_word_list))

                            if l_i < len(line["words"]) - 2:
                                next_word = create_uri("W", word_number, str(l_i + 1), stanza_number,
                                                  author, poem_title, dataset, stamp)
                                g.add((r_word, POETIC.nextWord, next_word))
                            if l_i > 0:
                                prev_word = create_uri("W", word_number, str(l_i - 1), stanza_number,
                                author, poem_title, dataset, stamp)
                                g.add(
                                    (r_word, POETIC.previousWord, prev_word))

                            if "syllables" in word.keys():
                                # Create syllable list
                                r_syllable_list = create_uri("GSL", stanza_number, str(l_i), author, poem_title, dataset, stamp)
                                g.add((r_syllable_list, RDF.type, POETIC.GrammaticalSyllableList))
                                g.add((r_syllable_list, POETIC.numberOfGrammaticalSyllables, Literal(len(word["syllables"]), datatype=XSD.nonNegativeInteger)))
                                # Add Syllable List to Line
                                g.add((r_line, POETIC.hasGrammaticalSyllableList, r_syllable_list))
                                g.add((r_syllable_list,
                                       POETIC.isGrammaticalSyllableListOf,
                                       r_line))
                                # Add Syllable List to Scansion
                                g.add((r_scansion, POETIC.hasListAnnotation, r_syllable_list))

                                for s_i, syllable in enumerate(word["syllables"]):
                                    # syllable_number = str(s_i)
                                    syllable_number = count_syllables
                                    r_syllable = create_uri("GSY", str(count_syllables),
                                                                  word_number, str(l_i),
                                                                  stanza_number, author,
                                                                  poem_title, dataset, stamp)
                                    # Add Syllable type
                                    g.add((r_syllable, RDF.type, POETIC.GrammaticalSyllable))
                                    # Add Syllable to line
                                    g.add((r_line, POETIC.hasGrammaticalSyllable, r_syllable))
                                    g.add((r_syllable,
                                           POETIC.isGrammaticalSyllableOf,
                                           r_line))
                                    # Add analyses word link
                                    g.add((r_word, POETIC.isWordAnalysedBy, r_syllable))
                                    g.add((r_syllable,
                                           POETIC.analysesWord,
                                           r_line))
                                    # Add Syllable DP
                                    g.add((r_syllable, POETIC.grammaticalSyllableNumber,
                                           Literal(syllable_number,
                                                   datatype=XSD.nonNegativeInteger)))
                                    g.add((r_syllable, POETIC.content, Literal(syllable,
                                                                               datatype=XSD.string)))
                                    # Add Syllable to list
                                    g.add((r_syllable_list, POETIC.grammaticalSyllable, r_syllable))
                                    g.add((r_syllable,
                                           POETIC.grammaticalSyllableList,
                                           r_syllable_list))

                                    if syllable_number == 0:
                                        g.add((r_syllable_list, POETIC.firstGrammaticalSyllable, r_syllable))
                                        g.add((r_syllable, POETIC.firstGrammaticalSyllableOf, r_syllable_list))
                                    elif syllable_number == tot_syllables - 1:
                                        g.add((r_syllable_list, POETIC.lastGrammaticalSyllable, r_syllable))
                                        g.add((r_syllable, POETIC.lastGrammaticalSyllableOf, r_syllable_list))

                                    if syllable_number < tot_syllables - 1:
                                        next_syl = create_uri("GSY", str(count_syllables + 1),
                                                                  word_number, str(l_i),
                                                                  stanza_number, author,
                                                                  poem_title, dataset, stamp)
                                        g.add((r_syllable, POETIC.nextGrammaticalSyllable, next_syl))
                                    if syllable_number > 0:
                                        prev_syl = create_uri("GSY", str(count_syllables - 1),
                                                                  word_number, str(l_i),
                                                                  stanza_number, author,
                                                                  poem_title, dataset, stamp)
                                        g.add((r_syllable, POETIC.previousGrammaticalSyllable, prev_syl))

                                    count_syllables += 1

    return graph_name

# I suppose this is the output of the automatic scansion process
def add_rantanplan_elements(cj_store, scansion, poem_title, author, dataset, enjambments, n_doc) -> str:
    """Function to generate RDF triples from rantanplan scansion output for a
    poem.

    :param scansion: dict with rantanplan output
    :type scansion: dict
    :param poem_title: Title of the poem to be analyzed
    :type poem_title: str
    :param author: Author of the poem to be analyzed
    :type author: str
    :param dataset: Dataset of the poem to be analyzed
    :type dataset: str
    :return: Tuple including scansion uri and the Graph with the RDF triples compliant with
        POSTDATA Metrical Analysis ontology
    :rtype: Graph
    """
    # Scansion event
    f_time = str(time.time())
    stamp = f_time[0:10] + f_time[11:]
    # We won't have the names graphs in CLSCor though (IB)
    graph_name = "http://postdata.linhd.uned.es/A_" + slugify(
        author) + "_" + slugify(poem_title) + "_" + str(stamp)
    g = Graph(cj_store, graph_name)
    g_def = Graph(cj_store, "tag:stardog:api:context:default")

    # Create Scansion process (POSTDATA legacy)
    r_event_scansion = create_uri("SP", author, poem_title, dataset, stamp)
    g_def.add((r_event_scansion, RDFS.label, Literal(f"(POSTDATA) Automatic Scansion Process of '{author}: {poem_title}' using Rantanplan"))) 
    g_def.add((r_event_scansion, RDF.type, POETIC.ScansionProcess))
    
    # CLSCor: We consider the 'Scansion Process' rather a Digital Machine Event (dig) that operates on a Digtial File (d1); The Scansion in this case would be a
    # digital object as well
    # In the following I add a stub of a the parallel structure for CLSCor; It has still to be discussed, how to map between them
    # 'r_event_scansion' is similar to this:
    clscor_digital_analyis = URIRef(generate_clscor_uri(str(create_uri("AUTO_ANALYSIS_PROCESS", author, poem_title, dataset, stamp))))
    g_def.add((clscor_digital_analyis, RDF.type, DIG.D7_Digital_Machine_Event))
    g_def.add((clscor_digital_analyis, RDFS.label, Literal(f"(CLSCor) Automatic Analysis of '{author}: {poem_title}' using Rantanplan")))
    g_def.add((clscor_digital_analyis, CRM.P2_has_type, URIRef(CLSCOR_POSTDATA_TYPE_URIS["auto_analysis_w_rantanplan"])))
    g_def.add((URIRef(CLSCOR_POSTDATA_TYPE_URIS["auto_analysis_w_rantanplan"]), CRM.P2i_is_type_of, clscor_digital_analyis))

    # Associate agent to scansion process
    r_agent_role = create_uri("AR", "Rantanplan_v.0.6.0", poem_title, dataset, stamp)
    g_def.add((r_event_scansion, CORE.hasAgentRole, r_agent_role))
    g_def.add((r_agent_role, CORE.isAgentRoleOf, r_event_scansion))
    r_rantanplan_agent = URIRef(KOS + "Rantanplan")
    g_def.add((r_rantanplan_agent, RDFS.label, Literal("Rantanplan v.0.6.0")))
    g_def.add((r_rantanplan_agent, RDFS.seeAlso,
           URIRef("https://github.com/linhd-postdata/rantanplan")))
    
    # CLSCor: We consider "Rantanplan" a Tool; dig: D14_Software
    rantanplan_software = URIRef(generate_clscor_uri("pstdata/tool/rantanplan/v.0.6.0"))
    g_def.add((rantanplan_software, RDF.type, DIG.D14_Software))
    g_def.add((rantanplan_software, RDFS.label, Literal("Rantanplan v.0.6.0")))

    g_def.add((r_agent_role, CORE.hasAgent, r_rantanplan_agent))
    g_def.add((r_rantanplan_agent, CORE.isAgentOf, r_agent_role))
    r_annotation_role = URIRef(KOS + "AutomaticAnnotator")
    g_def.add((r_annotation_role, RDF.type, SKOS.Concept))
    g_def.add((r_annotation_role, RDFS.label, Literal("Automatic Annotator")))
    g_def.add((r_agent_role, CORE.roleFunction, r_annotation_role))
    r_spanish_syll = URIRef(KOS + "CompleteSpanishSyllabification")
    g_def.add((r_event_scansion, POETIC.employedTechnique, r_spanish_syll))
    g_def.add((r_spanish_syll, RDFS.label, Literal("Complete Spanish Syllabification")))
    # Scansion created by scansion process
    r_scansion = create_uri("SC", author, poem_title, dataset, stamp)
    g_def.add((r_scansion, RDF.type, POETIC.Scansion))
    g_def.add((r_event_scansion, POETIC.generated, r_scansion))
    g_def.add((r_scansion, POETIC.isGeneratedBy, r_event_scansion))
    # Type of scansion
    r_concept_auto_scansion = URIRef(KOS + slugify("AutomaticScansion"))
    g_def.add((r_scansion, POETIC.typeOfScansion, r_concept_auto_scansion))
    g_def.add((r_concept_auto_scansion, RDFS.label, Literal("Automatic Scansion")))

    # Add graph information
    # We don't have the Graph, I remove it here!
    # g_def.add((r_scansion, POETIC.graphName, URIRef(graph_name)))

    # SCANSION TO FILE ID
    if n_doc is not None:
        g.add((r_scansion, POETIC.id, Literal("poem_" + str(n_doc) + "_A")))

    # Resources
    legacy_r_redaction = create_uri("R", author, poem_title, dataset) # Legacy POSTDATA
    # Here the redaction URI is created (again use the technique employed in core)
    r_redaction = URIRef(generate_clscor_uri(str(legacy_r_redaction))) # CLSCore
    r_stanza_list = create_uri("SL", poem_title, author, dataset, stamp)

    # Scansion used redaction
    # (IB) this I think is conceptually not correct. 
    # It should use the digital file (F3 Manifestation, NOT the Expression=Redaction!)
    # I don't change it here for now for compatibility reasons, but create a prallel structure with Digital Machine Event and the stuff!
    g_def.add((r_event_scansion, POETIC.usedAsInput, r_redaction))
    g_def.add((r_redaction, POETIC.wasInputFor, r_event_scansion))
    # Scansion generated stanza list
    g.add((r_scansion, POETIC.hasListAnnotation, r_stanza_list))
    g.add((r_stanza_list, POETIC.isListAnnotationOf, r_scansion))

    #CLSCOR
    # clscor_digital_analyis is done with rantanplan, produces output? uses as input a digital file (JSON Averell)
    #JSON file (as done in core)
    #L10_had_input, L10i_was_input_of
    #L11_had_output, L11i_was_output_of
    # L23_used_software_or_firmware, L23i_was_software_or_firmware_used_by
    # Not sure, what the output is though
    #TODO: maybe output is a file or the named graph (that we don't have in the Triple Store)
    
    r_corpus_document_averell_json = URIRef(generate_clscor_uri(str(create_uri("NEW_F3_averell_json", author, poem_title))))
    g_def.add((clscor_digital_analyis, DIG.L10_had_input, r_corpus_document_averell_json))
    g_def.add((r_corpus_document_averell_json, DIG.L10i_was_input_of, clscor_digital_analyis))
    g_def.add((clscor_digital_analyis, DIG.L23_used_software_or_firmware, rantanplan_software))
    g_def.add((rantanplan_software, DIG.L23i_was_software_or_firmware_used_by, clscor_digital_analyis))
    
    # Add types
    g_def.add((r_redaction, RDF.type, CORE.Redaction))
    g.add((r_stanza_list, RDF.type, POETIC.StanzaList))
    # Add stanza list to scansion
    g.add((r_scansion, POETIC.hasStanzaList, r_stanza_list))
    g.add((r_stanza_list, POETIC.isStanzaListOf, r_scansion))

    # Add number of stanzas
    g.add((r_stanza_list, POETIC.numberOfStanzas, Literal(len(scansion))))
    
    # (IB:) The following is an experimental modeling which aims at "elevating" the result of the digital analysis process to the Text (Expression); 
    # i.e. a statement/assertion about a text based on a digital analysis process
    number_of_stanza_assertion = URIRef(generate_clscor_uri(str(create_uri("E13_NUM_OF_STANZAS", author, poem_title))))
    
    g.add((number_of_stanza_assertion, RDF.type, CRM.E13_Attribute_Assignment))
    g.add((number_of_stanza_assertion, RDFS.label, Literal(f"Assertion about the number of stanzas in '{author}: {poem_title}' based on digital analysis with Rantanplan")))

    # Base of argument (P134_continued): This is experimental
    g.add((number_of_stanza_assertion, CRM.P134_continued, clscor_digital_analyis))
    g.add((clscor_digital_analyis, CRM.P134i_was_continued_by, number_of_stanza_assertion))

    number_of_stanzas_dimension = URIRef(generate_clscor_uri(str(create_uri("E45_NUM_OF_STANZAS", author, poem_title))))
    
    g.add((number_of_stanzas_dimension, RDF.type, CRM.E54_Dimension))
    g.add((number_of_stanzas_dimension, RDFS.label, Literal(f"Number of stanzas in '{author}: {poem_title}' [Calculated Value]")))
    g.add((number_of_stanzas_dimension, CRM.P90_has_value, Literal(len(scansion), datatype=XSD.Integer)))
    
    unit_stanza = URIRef(generate_clscor_uri("unit/segment/stanza"))
    g.add((unit_stanza, RDF.type, CLS.X3_Feature))
    g.add((unit_stanza, RDFS.label, Literal("Stanza [Feature: Measurement Unit, Type]")))

    g.add((number_of_stanzas_dimension, CRM.P91_has_unit, unit_stanza))
    g.add((unit_stanza, CRM.P91i_is_unit_of, number_of_stanzas_dimension))

    g.add((number_of_stanza_assertion, CRM.P141_assigned, number_of_stanzas_dimension))
    g.add((number_of_stanzas_dimension, CRM.P141i_was_assigned_by, number_of_stanza_assertion))

    g.add((number_of_stanza_assertion, CRM.P140_assigned_attribute_to, r_redaction))
    g.add((r_redaction, CRM.P140i_was_attributed_by, number_of_stanza_assertion))

    line_count = 0
    # syllable_count = 0
    structure = None

    #clscor: (IB)
    # I would be interested in the overall number of verses, e.g. 14 --> maybe Sonnet, and the structure in a notation like 4-4-3-3
    # and "elevate" this to the text/expression/redaction as an assertion
    # e.g. https://poecor.org/corpora/postdata/jacinto-polo-de-medina_de-la-nieve-de-espuma
    # set this to get an overall number of lines of the poem
    overall_line_count = 0
    # have a variable that would hold the line counts per stanza
    line_counts_in_stanzas = []

    # Iterate over stanzas
    for st_index, stanza in enumerate(scansion):
        stanza_text = join_lines(stanza)
        r_stanza = create_uri("ST", str(st_index), author, poem_title, dataset, stamp)
        # r_stanza_pattern = create_uri("SP", st_index, author, poem_title, dataset, stamp)
        # Add Stanza Type
        g.add((r_stanza, RDF.type, POETIC.Stanza))
        # g.add((r_stanza_pattern, RDF.type, POETIC.StanzaPattern))
        # Add Stanza to StanzaList
        g.add((r_stanza_list, POETIC.stanza, r_stanza))
        g.add((r_stanza, POETIC.stanzaList, r_stanza_list))
        # Add Stanza to scansion
        g.add((r_scansion, POETIC.hasStanza, r_stanza))
        g.add((r_stanza, POETIC.isStanzaOf, r_scansion))

        # Add Stanza DP
        g.add((r_stanza, POETIC.content, Literal(stanza_text)))
        g.add((r_stanza, POETIC.stanzaNumber,
               Literal(st_index, datatype=XSD.nonNegativeInteger)))
        # Add Stanza DP (old pattern)
        g.add((r_stanza, POETIC.rhymeScheme,
               Literal(get_rhyme_pattern(stanza))))

        # Add first and last stanzas to list - Previous and Next Stanzas
        if st_index == 0:
            g.add((r_stanza_list, POETIC.firstStanza, r_stanza))
            g.add((r_stanza, POETIC.firstStanzaoF, r_stanza_list))
        else:
            prev_st_index = st_index - 1
            g.add((r_stanza, POETIC.previousStanza,
                   create_uri("ST", str(prev_st_index), author, poem_title,
                              dataset, stamp)))
        if st_index + 1 == len(scansion):
            g.add((r_stanza_list, POETIC.lastStanza, r_stanza))
            g.add((r_stanza, POETIC.lastStanzaOf, r_stanza_list))
        else:
            next_st_index = st_index + 1
            g.add((r_stanza, POETIC.nextStanza,
                   create_uri("ST", str(next_st_index), author, poem_title,
                              dataset, stamp)))

        # Create line list and add type
        r_line_list = create_uri("LL", poem_title, author, dataset, str(st_index), stamp)
        g.add((r_line_list, RDF.type, POETIC.LineList))
        
        
        g.add((r_line_list, POETIC.numberOfLines, Literal(len(stanza), datatype=XSD.nonNegativeInteger)))
        
        # (IB): This above seems the line count per stanza, store these to access them later; is at end of function
        overall_line_count = overall_line_count + len(stanza)
        line_counts_in_stanzas.append(len(stanza))
        
        # Add line list to scansion
        g.add((r_scansion, POETIC.hasListAnnotation, r_line_list))
        g.add((r_line_list, POETIC.isListAnnotationOf, r_scansion))
        # Add line list to stanza
        g.add((r_stanza, POETIC.hasLineList, r_line_list))
        g.add((r_line_list, POETIC.isLineListOf, r_stanza))

        ### ADD RHYMES ###
        rhymes_list = [(get_last_word_index(line["tokens"]), line["rhyme"], line["rhyme_type"], line["ending"], line_index) for line_index, line in enumerate(stanza)]
        # Add rhyme info - last Word of Line, add Rhyme to the Word URIRef
        for (w_ind, rhyme_label, rhyme_type, rhyme_ending, line_index) in rhymes_list:
            print(w_ind, rhyme_label, rhyme_type, rhyme_ending, line_index)
            if rhyme_label != "-":
                # Rhyme is denoted by a label
                r_rhyme = create_uri("R", rhyme_label, poem_title, author, poem_title, dataset, stamp)
                g.add((r_rhyme, RDF.type, POETIC.Rhyme))
                g.add((r_rhyme, POETIC.rhymeLabel, Literal(rhyme_label)))

                r_line = create_uri("L", str(line_index), str(st_index), author,
                                    poem_title,
                                    dataset, stamp)

                # Associate current line to the rhyme (label set x stanza)
                g.add((r_line, POETIC.presentsRhyme, r_rhyme))
                g.add((r_rhyme, POETIC.isRhymePresentAt, r_line))

                # Look for rhyme matchings
                prev_indexes = [i for i in range(0, line_index-1)]
                prev_indexes.reverse()
                prev_objects = [rhymes_list[j] for j in prev_indexes]
                # print("Indexes", line_index, prev_objects)
                # For line in the previous lines of the stanza, look for same label
                for j in prev_objects:
                    if j[1] == rhyme_label:
                        # Create Rhyme match if labels match for a previous line in same stanza
                        prev_word_line_index = j[4]
                        prev_word_index = j[0]

                        r_prev_line = create_uri("L", str(prev_word_line_index), str(st_index), author,
                                    poem_title,
                                    dataset, stamp)
                        r_prev_word = create_uri("W", str(prev_word_index), str(r_prev_line), str(st_index),
                                        author, poem_title, dataset, stamp)

                        r_next_word = create_uri("W", str(w_ind),
                                                 str(line_index), str(st_index),
                                                 author, poem_title, dataset,
                                                 stamp)

                        r_rhyme_match = create_uri("RM", poem_title, author, dataset, rhyme_label, str(prev_word_line_index), str(line_index), stamp)
                        g.add((r_rhyme_match, RDF.type, POETIC.RhymeMatch))
                        g.add((r_rhyme, POETIC.hasRhymeMatch, r_rhyme_match))
                        g.add((r_rhyme_match, POETIC.isRhymeMatchOf, r_rhyme))

                        g.add((r_rhyme_match, POETIC.rhymeGrapheme, Literal(rhyme_ending)))

                        g.add((r_rhyme_match, POETIC.hasCallWord, r_prev_word))
                        g.add((r_prev_word, POETIC.isCallWordIn, r_rhyme_match))

                        g.add((r_rhyme_match, POETIC.hasEchoWord, r_next_word))
                        g.add((r_next_word, POETIC.isEchoWordIn, r_rhyme_match))

                        g.add((r_rhyme_match, POETIC.hasEchoLine, r_line))
                        g.add((r_line, POETIC.isEchoLineIn, r_rhyme_match))

                        g.add((r_rhyme_match, POETIC.hasCallLine, r_prev_line))
                        g.add((r_prev_line, POETIC.isCallLineIn, r_rhyme_match))

                        g.add((r_next_word, POETIC.isEchoOf, r_prev_word))
                        g.add((r_prev_word, POETIC.isCallOf, r_next_word))

                        r_rtype = URIRef(KOS + slugify(rhyme_type))

                        # Add line rhymes with line
                        g.add((r_line, POETIC.rhymesWith, r_prev_line))

                        # Add rhyme matching type
                        g.add((r_rhyme_match, POETIC.typeOfRhymeMatching, r_rtype))
                        g.add((r_rtype, RDF.type, SKOS.concept))
                        g.add((r_rtype, RDFS.label, Literal(rhyme_type)))
                        break
        ##### RHYMES END #####

        # Iterate over lines
        for l_index, line in enumerate(stanza):
            # Create line
            r_line = create_uri("L", str(line_count), str(st_index), author,
                                poem_title,
                                dataset, stamp)
            # Create lists
            r_word_list = create_uri("WL", str(l_index), str(st_index), author,
                                     poem_title,
                                     dataset, stamp)
            r_punctuation_list = create_uri("PL", str(l_index), str(st_index), author,
                                            poem_title,
                                            dataset, stamp)
            r_grammatical_list = create_uri("GSL", str(l_index), str(st_index), author,
                                            poem_title,
                                            dataset, stamp)
            r_metrical_list = create_uri("MSL", str(l_index), str(st_index), author,
                                         poem_title,
                                         dataset, stamp)

            # Add types
            g.add((r_line, RDF.type, POETIC.Line))
            g.add((r_word_list, RDF.type, POETIC.WordList))
            g.add((r_grammatical_list, RDF.type,
                   POETIC.GrammaticalSyllableList))
            g.add((r_metrical_list, RDF.type, POETIC.MetricalSyllableList))
            # g.add((r_line_pattern, RDF.type, POETIC.LinePattern))
            g.add((r_punctuation_list, RDF.type, POETIC.PunctuationList))
            # Add patterns to scansion
            # g.add((r_scansion, POETIC.hasPatternAnnotation, r_line_pattern))
            # g.add((r_line_pattern, POETIC.isPatternAnnotationOf, r_scansion))
            # Add lists to scansion
            g.add((r_scansion, POETIC.hasListAnnotation, r_word_list))
            g.add((r_word_list, POETIC.isListAnnotationOf, r_scansion))
            g.add((r_scansion, POETIC.hasListAnnotation, r_punctuation_list))
            g.add((r_punctuation_list, POETIC.isListAnnotationOf, r_scansion))
            g.add((r_scansion, POETIC.hasListAnnotation, r_metrical_list))
            g.add((r_metrical_list, POETIC.isListAnnotationOf, r_scansion))
            g.add((r_scansion, POETIC.hasListAnnotation, r_grammatical_list))
            g.add((r_grammatical_list, POETIC.isListAnnotationOf, r_scansion))

            # Add line to stanza - Add first and last lines to stanza
            g.add((r_stanza, POETIC.hasLine, r_line))
            g.add((r_line, POETIC.isLineOf, r_stanza))

            # Add line to line list
            g.add((r_line_list, POETIC.line, r_line))
            g.add((r_line, POETIC.lineList, r_line_list))
            # Add lists to line
            g.add((r_line, POETIC.hasWordList, r_word_list))
            g.add((r_word_list, POETIC.isWordListOf, r_line))
            g.add((r_line, POETIC.hasGrammaticalSyllableList,
                   r_grammatical_list))
            g.add((r_grammatical_list, POETIC.isGramamticalSyllableListOf,
                   r_line))
            g.add((r_line, POETIC.hasMetricalSyllableList, r_metrical_list))
            g.add((r_metrical_list, POETIC.isMetricalSyllableListOf, r_line))

            # Add pattern to line
            # g.add((r_line, POETIC.hasLinePattern, r_line_pattern))
            # g.add((r_line_pattern, POETIC.isLinePatternOf, r_line))

            # Add Enjambments to the line
            if enjambments.get(line_count):
                # print(enjambments.get(line_count))
                r_enjambment = create_uri("ENJ", str(line_count), str(st_index), author, poem_title, dataset, stamp)
                g.add((r_enjambment, RDF.type, POETIC.Enjambment))
                g.add((r_enjambment, POETIC.affectsLine, r_line))
                g.add((r_line, POETIC.isLineAffectedBy, r_enjambment))
                enjmb_type = enjambments.get(line_count).get("type")
                r_enjambment_type = URIRef(KOS + slugify(enjmb_type))
                g.add((r_enjambment, POETIC.typeOfEnjambment, r_enjambment_type))
                g.add((r_enjambment_type, RDFS.label, Literal(enjmb_type)))

                # Add enjambment to scansion
                g.add((r_scansion, POETIC.hasDeviceAnnotation, r_enjambment))
                g.add((r_enjambment, POETIC.isDeviceAnnotationOf, r_scansion))

            # Add line DP indexes
            g.add((r_line, POETIC.relativeLineNumber,
                   Literal(l_index, datatype=XSD.nonNegativeInteger)))
            g.add((r_line, POETIC.absoluteLineNumber,
                   Literal(str(line_count), datatype=XSD.nonNegativeInteger)))
            # Add metrical pattern to line (old pattern)
            g.add((r_line, POETIC.patterningMetricalScheme,
                   Literal(line["rhythm"]["stress"], datatype=XSD.string)))
            # Check for Stanza type
            if not structure and line.get("structure") is not None:
                structure = line["structure"]
                r_stype = URIRef(KOS + slugify(structure))
                g.add((r_stanza, POETIC.metricalType, r_stype))
                g.add((r_stype, RDFS.label, Literal(structure)))

            if "tokens" not in line:
                continue

            # Add line text
            line_text = join_tokens(line["tokens"])
            g.add((r_line, POETIC.content, Literal(line_text)))
            # Add grammatical pattern to line (old pattern)
            g.add((r_line, POETIC.grammaticalStressPattern,
                   Literal(get_grammatical_stress_pattern(line["tokens"]),
                           datatype=XSD.string)))

            # Add first last lines to line list - Add previous next Line links
            if line_count == 0:
                g.add((r_line_list, POETIC.firstLine, r_line))
                g.add((r_line, POETIC.firstLineOf, r_line_list))
            else:
                g.add((r_line, POETIC.previousLine,
                       create_uri("L", str(line_count - 1), str(st_index), author,
                                  poem_title,
                                  dataset, stamp)))
            if int(st_index) + 1 == len(scansion) and int(l_index) + 1 == len(stanza):
                g.add((r_line_list, POETIC.lastLine, r_line))
                g.add((r_line, POETIC.lastLineOf, r_line_list))
            else:
                g.add((r_line, POETIC.nextLine,
                       create_uri("L", str(line_count + 1), str(st_index), author,
                                  poem_title, dataset, stamp)))

            word_count = 0  # Relative to Line
            punct_count = 0
            gram_syll_count = 0
            total_words = 0
            for token in line["tokens"]:
                if "word" in token:
                    total_words = total_words + 1
            # Iterate over words
            for w_index, token in enumerate(line["tokens"]):
                if "symbol" in token:
                    r_punct = create_uri("P", str(punct_count), str(l_index), str(st_index),
                                         author, poem_title, dataset, stamp)
                    # Add punctuation to line
                    g.add((r_line, POETIC.hasPunctuation, r_punct))
                    g.add((r_punct, POETIC.isPunctuationOf, r_line))
                    # Add punctuation to punctuation list
                    g.add((r_punctuation_list, POETIC.punctuation, r_punct))
                    g.add((r_punct, POETIC.punctuationList, r_punctuation_list))
                    # Add punctuation content
                    g.add((r_punct, POETIC.content, Literal(token["symbol"])))
                    # Add punctuation beofe/after word
                    if word_count > 0:
                        r_prev_word = create_uri("W", str(word_count-1), str(l_index),
                                                 str(st_index), author, poem_title,
                                                 dataset, stamp)
                        g.add((r_punct, POETIC.after, r_prev_word))
                    if w_index != len(line["tokens"]):
                        r_next_word = create_uri("W", str(word_count), str(l_index),
                                                 str(st_index), author, poem_title,
                                                 dataset, stamp)
                        g.add((r_punct, POETIC.before, r_next_word))
                    # Add previous and next punctuations
                    if punct_count > 0:
                        # Add previous
                        r_prev_punct = create_uri("P", str(punct_count-1), str(l_index), str(st_index),
                                         author, poem_title, dataset, stamp)
                        g.add((r_punct, POETIC.previousPunctuation, r_prev_punct))
                        # Add next from previous
                        g.add((r_prev_punct, POETIC.nextPunctuation, r_punct))

                    punct_count += 1
                elif "word" in token:
                    word_text = join_syllables(token)
                    # Create word resource
                    r_word = create_uri("W", str(word_count), str(l_index), str(st_index),
                                        author, poem_title, dataset, stamp)
                    # Add word type
                    g.add((r_word, RDF.type, POETIC.Word))
                    # Add word to WordList
                    g.add((r_word_list, POETIC.word, r_word))
                    g.add((r_word, POETIC.wordList, r_word_list))
                    # Add word to Line
                    g.add((r_line, POETIC.hasWord, r_word))
                    g.add((r_word, POETIC.isWordOf, r_line))

                    # Add Word DP
                    # print("WORD TEXT", word_text, token)
                    g.add((r_word, POETIC.content, Literal(word_text)))
                    g.add((r_word, POETIC.wordNumber,
                           Literal(str(word_count), datatype=XSD.nonNegativeInteger)))

                    if word_count == 0:
                        g.add((r_word_list, POETIC.firstWord, r_word))
                        g.add((r_word, POETIC.firstWordOf, r_word_list))
                    else:
                        prev_w_index = word_count - 1
                        g.add((r_word, POETIC.previousWord,
                               create_uri("W", str(prev_w_index), str(l_index), str(st_index),
                                          author, poem_title, dataset, stamp)))
                    if word_count + 1 == total_words:
                        g.add((r_word_list, POETIC.lastWord, r_word))
                        g.add((r_word, POETIC.lastWordOf, r_word_list))
                    else:
                        next_w_index = word_count + 1
                        g.add((r_word, POETIC.nextWord,
                               create_uri("W", str(next_w_index), str(l_index), str(st_index),
                                          author, poem_title, dataset, stamp)))

                    for sy_index_word, syllable in enumerate(token["word"]):
                        # Iterate over Grammatical syllables
                        # for sy_index_word, syllable in enumerate(token['word']):
                        # print("GSYLL", gram_syll_count, syllable)

                        r_syllable = create_uri("GSY", str(gram_syll_count), str(word_count), str(l_index),
                                                str(st_index), author, poem_title,
                                                dataset, stamp)
                        # Add Gram Syllable type
                        g.add((r_syllable, RDF.type, POETIC.GrammaticalSyllable))
                        # Add Gram Syllable to line
                        g.add((r_line, POETIC.hasGrammaticalSyllable, r_syllable))
                        g.add((r_syllable, POETIC.isGrammaticalSyllableOf, r_line))
                        # Add Gram Syllable analyses word
                        g.add((r_word, POETIC.isWordAnalysedBy, r_syllable))
                        g.add((r_syllable, POETIC.analysesWord, r_word))
                        # Add Gram Syllable to Gram Syllable List
                        g.add((r_grammatical_list, POETIC.grammaticalSyllable, r_syllable))
                        g.add((r_syllable, POETIC.grammaticalSyllableList,
                               r_grammatical_list))

                        # Add Syllable DP
                        g.add((r_syllable, POETIC.grammaticalSyllableNumber,
                               Literal(gram_syll_count,
                                       datatype=XSD.nonNegativeInteger)))
                        g.add((r_syllable, POETIC.content,
                               Literal(syllable["syllable"],
                                       datatype=XSD.string)))
                        g.add((r_syllable, POETIC.isStressed,
                               Literal(syllable["is_stressed"],
                                       datatype=XSD.boolean)))
                        # first last previous next Gram Syllable
                        if gram_syll_count == 0:
                            g.add((r_grammatical_list,
                                   POETIC.firstGrammaticalSyllable, r_syllable))
                            g.add((r_syllable,
                                   POETIC.firstGrammaticalSyllableOf, r_grammatical_list))
                        elif gram_syll_count > 0:
                            prev_sy_index = gram_syll_count - 1
                            g.add((r_syllable, POETIC.previousGrammaticalSyllable,
                                   create_uri("GSY", str(prev_sy_index), str(word_count),
                                              str(l_index), str(st_index), author, poem_title,
                                              dataset, stamp)))
                        if gram_syll_count + 1 == len(token["word"]):
                            g.add((r_grammatical_list,
                                   POETIC.lastGrammaticalSyllable, r_syllable))
                            g.add((r_syllable,
                                   POETIC.lastGrammaticalSyllableOf, r_grammatical_list))
                        else:
                            next_sy_index = gram_syll_count + 1
                            g.add((r_syllable, POETIC.nextGrammaticalSyllable,
                                   create_uri("GSY", str(next_sy_index), str(word_count),
                                              str(l_index), str(st_index), author, poem_title,
                                              dataset, stamp)))
                        gram_syll_count = gram_syll_count + 1
                    word_count = word_count + 1

            # Group grammatical syllables
            all_gram_syllables = []
            w_count = 0
            g_s_count = 0
            new_tokens = include_dieresis(line["tokens"], line["phonological_groups"])
            print("NEW TOKENS!", new_tokens)
            for w_ind, token in enumerate(new_tokens):
                # print(token)
                if "word" in token.keys():
                    for s_ind, syll in enumerate(token["word"]):
                        # print(syll)
                        has_synalepha = False
                        has_dieresis = False
                        has_sinaeresis = False
                        dieresis_index = -1
                        if "has_synalepha" in syll.keys() and syll["has_synalepha"] == True:
                            has_synalepha = True
                        if "has_dieresis" in syll.keys() and syll["has_dieresis"] == True:
                            has_dieresis = True
                            dieresis_index = syll["dieresis_index"]
                        if "has_sinaeresis" in syll.keys() and syll["has_sinaeresis"] == True:
                            has_sinaeresis = True
                        all_gram_syllables.append({"w_number": w_count,
                                                        "content": syll["syllable"],
                                                       "s_number": g_s_count,
                                                       "synalepha": has_synalepha,
                                                        "dieresis": has_dieresis,
                                                        "dieresis_index": dieresis_index,
                                                        "sinaeresis": has_sinaeresis,
                                                       "is_stressed": syll["is_stressed"]})
                        g_s_count = g_s_count + 1
                    w_count = w_count + 1

            all_gram_syllables_index = 0
            metsyll_list_length = len(line["phonological_groups"])
            print("ALL GRAM", all_gram_syllables)
            # print("MET SYLLS", line["phonological_groups"])

            # ADD metrical syllables
            for msyl_index, msyl in enumerate(line["phonological_groups"]):
                # print("MET_SYLL", msyl_index, msyl)
                # Create Met Syllable Resource and add type
                r_metsyll = create_uri("MSY", str(msyl_index), str(l_index),
                                            str(st_index), author, poem_title,
                                            dataset, stamp)
                # Add type
                g.add((r_metsyll, RDF.type, POETIC.MetricalSyllable))

                # Add metricalSyllable phoneticTranscription
                g.add((r_metsyll, POETIC.phoneticTranscription, Literal(msyl["syllable"])))

                # Add Met Syllable to Met Syllable List
                g.add((r_metrical_list, POETIC.metricalSyllable, r_metsyll))
                g.add((r_metsyll, POETIC.metricalSyllableList, r_metrical_list))

                # Add Met Syllable to Line
                g.add((r_line, POETIC.hasMetricalSyllable, r_metsyll))
                g.add((r_metsyll, POETIC.isMetricalSyllableOf, r_line))
                # Add Met Syllable list to line
                # g.add((r_line, POETIC.hasMetricalSyllableList, r_metrical_list))
                # g.add((r_metrical_list, POETIC.isMetricalSyllableListOf, r_line))

                # Add DP - Stress and number
                g.add((r_metsyll, POETIC.isStressed,
                       Literal(msyl["is_stressed"],
                               datatype=XSD.boolean)))
                g.add((r_metsyll, POETIC.metricalSyllableNumber,
                       Literal(msyl_index,
                               datatype=XSD.nonNegativeInteger)
                       ))

                # Add first/last to list - Add next and prev links MetSyllables
                if msyl_index == 0:
                    g.add((r_metrical_list, POETIC.firstMetricalSyllable, r_metsyll))
                    g.add((r_metsyll, POETIC.firstMetricalSyllableOf,
                           r_metrical_list))
                if msyl_index > 0:
                    r_prev_metsyll = create_uri("MSY", str(msyl_index - 1),
                                                 str(l_index),
                                                 str(st_index), author, poem_title,
                                                 dataset, stamp)
                    g.add((r_metsyll, POETIC.previousMetricalSyllable, r_prev_metsyll))
                    if msyl_index == metsyll_list_length - 1:
                        g.add((r_metrical_list, POETIC.lastMetricalSyllable,
                               r_metsyll))
                        g.add((r_metsyll, POETIC.lastMetricalSyllableOf,
                               r_metrical_list))
                if msyl_index < metsyll_list_length - 1:
                    r_next_met_syll = create_uri("MSY", str(msyl_index + 1),
                                                 str(l_index),
                                                 str(st_index), author,
                                                 poem_title,
                                                 dataset, stamp)
                    g.add((r_metsyll, POETIC.nextMetricalSyllable, r_next_met_syll))

            # Add analyses links and metaplasms
            phonological_groups = line["phonological_groups"]
            met_syll_count = 0
            synalepha_counter = 0
            r_sinalepha = URIRef(KOS + slugify("Synalepha"))
            r_sinaeresis = URIRef(KOS + slugify("Sinaeresis"))
            r_dieresis = URIRef(KOS + slugify("Dieresis"))

            print("ALL GRAM", all_gram_syllables)
            print("PHONOLOGICAL", phonological_groups)

            for gram_syll_index, gram_syll in enumerate(all_gram_syllables):
                r_curr_gram_syll = create_uri("GSY", str(gram_syll["s_number"]),
                                              str(gram_syll["w_number"]),
                                              str(l_index), str(st_index),
                                              author, poem_title, dataset, stamp)
                r_curr_met_syll = create_uri("MSY", str(met_syll_count),
                                                 str(l_index),
                                                 str(st_index), author,
                                                 poem_title,
                                                 dataset, stamp)
                r_curr_word = create_uri("W", str(gram_syll["w_number"]), str(l_index),
                                                 str(st_index), author, poem_title,
                                                 dataset, stamp)

                print("MET_SYLL_COUNT", met_syll_count)

                if synalepha_counter > 0 and gram_syll["sinaeresis"] is False:
                    synalepha_counter = synalepha_counter - 1
                    # Add analyses between current gram_syll and current met_syll
                    g.add((r_curr_met_syll, POETIC.analysesGrammaticalSyllable,
                           r_curr_gram_syll))
                    g.add((r_curr_gram_syll,
                           POETIC.isGrammaticalSyllableAnalysedBy,
                           r_curr_met_syll))
                    print(gram_syll["content"], "<--->",
                          phonological_groups[met_syll_count], "SYN2")
                    if synalepha_counter == 0:
                        met_syll_count = met_syll_count + 1
                    # continue
                elif "synalepha_index" in phonological_groups[met_syll_count]:
                    synalepha_counter = len(phonological_groups[met_syll_count]["synalepha_index"])
                    # Add analyses between current gram_syll and current met_syll
                    g.add((r_curr_met_syll, POETIC.analysesGrammaticalSyllable, r_curr_gram_syll))
                    g.add((r_curr_gram_syll, POETIC.isGrammaticalSyllableAnalysedBy, r_curr_met_syll))
                    # Create metaplasm
                    r_metaplasm = create_uri("MET-SYN", str(gram_syll["s_number"]),
                                             str(l_index), str(st_index),
                                             author, poem_title, dataset,
                                             stamp)
                    g.add((r_metaplasm, POETIC.typeOfMetaplasm, r_sinalepha))
                    g.add((r_sinalepha, RDFS.label, Literal("Synalepha")))
                    g.add((r_sinalepha, RDF.type, SKOS.Concept))
                    # Add metaplasm to gram_syll
                    g.add((r_curr_gram_syll,
                           POETIC.isFirstGrammaticalSyllableAffectedBy,
                           r_metaplasm))
                    g.add((r_metaplasm, POETIC.affectsFirstGrammaticalSyllable,
                           r_curr_gram_syll))
                    # Add metaplasm to word
                    g.add((r_metaplasm, POETIC.affectsFirstWord, r_curr_word))
                    g.add((r_curr_word, POETIC.isFirstWordAffectedBy, r_metaplasm))
                    # Add metaplasm to scansion
                    g.add((r_scansion, POETIC.hasDeviceAnnotation, r_metaplasm))
                    g.add((r_metaplasm, POETIC.isDeviceAnnotationOf, r_scansion))
                    print(gram_syll["content"], "<--->",
                          phonological_groups[met_syll_count], "SYN1")
                    # continue
                elif "sinaeresis_index" in phonological_groups[met_syll_count]:
                    # Add analyses between current gram_syll and current met_syll
                    g.add((r_curr_met_syll, POETIC.analysesGrammaticalSyllable,
                           r_curr_gram_syll))
                    g.add((r_curr_gram_syll,
                           POETIC.isGrammaticalSyllableAnalysedBy,
                           r_curr_met_syll))
                    # Create metaplasm
                    r_metaplasm = create_uri("MET-SIN", str(gram_syll["s_number"]),
                                             str(l_index), str(st_index),
                                             author, poem_title, dataset,
                                             stamp)
                    g.add((r_metaplasm, POETIC.typeOfMetaplasm, r_sinaeresis))
                    g.add((r_sinaeresis, RDFS.label, Literal("Sinéresis")))
                    g.add((r_sinaeresis, RDF.type, SKOS.Concept))
                    # Add metaplasm to gram_syll
                    g.add((r_curr_gram_syll,
                           POETIC.isFirstGrammaticalSyllableAffectedBy,
                           r_metaplasm))
                    g.add((r_metaplasm, POETIC.affectsFirstGrammaticalSyllable,
                           r_curr_gram_syll))
                    # Add metaplasm to word
                    g.add((r_metaplasm, POETIC.affectsFirstWord, r_curr_word))
                    g.add((r_curr_word, POETIC.isFirstWordAffectedBy,
                           r_metaplasm))
                    # Add metaplasm to scansion
                    g.add((r_scansion, POETIC.hasDeviceAnnotation, r_metaplasm))
                    g.add((r_metaplasm, POETIC.isDeviceAnnotationOf, r_scansion))
                    print(gram_syll["content"], "<--->",
                          phonological_groups[met_syll_count], "SIN1")
                    #continue
                elif gram_syll["sinaeresis"]:
                    # Add analyses between current gram_syll and current met_syll
                    g.add((r_curr_met_syll,
                           POETIC.analysesGrammaticalSyllable,
                           r_curr_gram_syll))
                    g.add((r_curr_gram_syll,
                           POETIC.isGrammaticalSyllableAnalysedBy,
                           r_curr_met_syll))
                    # Create metaplasm
                    r_metaplasm = create_uri("MET-SIN",
                                             str(gram_syll["s_number"]),
                                             str(l_index), str(st_index),
                                             author, poem_title, dataset,
                                             stamp)
                    g.add((r_metaplasm, POETIC.typeOfMetaplasm,
                           r_sinaeresis))
                    g.add((r_sinaeresis, RDFS.label, Literal("Sinéresis")))
                    g.add((r_sinaeresis, RDF.type, SKOS.Concept))
                    # Add metaplasm to gram_syll
                    g.add((r_curr_gram_syll,
                           POETIC.isFirstGrammaticalSyllableAffectedBy,
                           r_metaplasm))
                    g.add((r_metaplasm,
                           POETIC.affectsFirstGrammaticalSyllable,
                           r_curr_gram_syll))
                    # Add metaplasm to word
                    g.add((r_metaplasm, POETIC.affectsFirstWord,
                           r_curr_word))
                    g.add((r_curr_word, POETIC.isFirstWordAffectedBy,
                           r_metaplasm))
                    # Add metaplasm to scansion
                    g.add((r_scansion, POETIC.hasDeviceAnnotation,
                           r_metaplasm))
                    g.add((r_metaplasm, POETIC.isDeviceAnnotationOf,
                           r_scansion))
                    print(gram_syll["content"], "<--->",
                          phonological_groups[met_syll_count], "SIN1")
                    # If previous gram_syll is affected by synalepha and the
                    # next gram syll is affected by a sinaeresis, end the
                    # (consecutive) synalephas.
                    if synalepha_counter == 1:
                        synalepha_counter = 0
                    # continue
                elif gram_syll["dieresis"]:
                    # Add analyses between current gram_syll and current met_syll
                    g.add((r_curr_met_syll, POETIC.analysesGrammaticalSyllable,
                           r_curr_gram_syll))
                    g.add((r_curr_gram_syll,
                           POETIC.isGrammaticalSyllableAnalysedBy,
                           r_curr_met_syll))
                    # Add analyses between current gram_syll and met_syll + 1
                    r_next_met_syll = create_uri("MSY", str(met_syll_count+1),
                                                 str(l_index),
                                                 str(st_index), author,
                                                 poem_title,
                                                 dataset, stamp)
                    g.add((r_next_met_syll, POETIC.analysesGrammaticalSyllable,
                           r_curr_gram_syll))
                    g.add((r_curr_gram_syll,
                           POETIC.isGrammaticalSyllableAnalysedBy,
                           r_next_met_syll))
                    # Create metaplasm
                    r_metaplasm = create_uri("MET-DIE", str(gram_syll["s_number"]),
                                             str(l_index), str(st_index),
                                             author, poem_title, dataset,
                                             stamp)
                    g.add((r_metaplasm, POETIC.typeOfMetaplasm, r_dieresis))
                    g.add((r_dieresis, RDFS.label, Literal("Diéresis")))
                    g.add((r_dieresis, RDF.type, SKOS.Concept))
                    index = gram_syll["dieresis_index"]
                    g.add((r_metaplasm, POETIC.metaplasmIndex, Literal(index, datatype=XSD.nonNegativeInteger)))
                    # Add metaplasm to gram_syll
                    g.add((r_curr_gram_syll,
                           POETIC.isFirstGrammaticalSyllableAffectedBy,
                           r_metaplasm))
                    g.add((r_metaplasm, POETIC.affectsFirstGrammaticalSyllable,
                           r_curr_gram_syll))
                    # Add metaplasm to word
                    g.add((r_metaplasm, POETIC.affectsFirstWord, r_curr_word))
                    g.add((r_curr_word, POETIC.isFirstWordAffectedBy,
                           r_metaplasm))
                    # Add metaplasm to scansion
                    g.add((r_scansion, POETIC.hasDeviceAnnotation, r_metaplasm))
                    g.add((r_metaplasm, POETIC.isDeviceAnnotationOf, r_scansion))
                    print(gram_syll["content"], "<--->",
                          phonological_groups[met_syll_count], "DI1")
                    print(gram_syll["content"], "<--->",
                          phonological_groups[met_syll_count+1], "DI2")
                    met_syll_count = met_syll_count + 2
                    # continue
                else:
                    # Add analyses between current gram_syll and current met_syll
                    g.add((r_curr_met_syll, POETIC.analysesGrammaticalSyllable, r_curr_gram_syll))
                    g.add((r_curr_gram_syll, POETIC.isGrammaticalSyllableAnalysedBy, r_curr_met_syll))
                    print(r_curr_gram_syll, r_curr_met_syll)
                    print(gram_syll["content"], "<--->",
                          phonological_groups[met_syll_count], "LAST")
                    met_syll_count = met_syll_count + 1
            line_count += 1

    # this seems to be the end of processing each stanza (IB)
    # For CLSCor we want to get the overall number of lines + the lines in stanza structure on "elevated" to the expression/the text
    # overall_line_count 
    # line_counts_in_stanzas

    # Use the Attribute Assignment pattern as for the Number of Stanzas
    # (IB:) The following is an experimental modeling which aims at "elevating" the result of the digital analysis process to the Text (Expression); 
    # i.e. a statement/assertion about a text based on a digital analysis process
    overall_number_of_verse_lines_assertion = URIRef(generate_clscor_uri(str(create_uri("E13_OVERALL_NUM_OF_LINES", author, poem_title))))
    
    g.add((overall_number_of_verse_lines_assertion, RDF.type, CRM.E13_Attribute_Assignment))
    g.add((overall_number_of_verse_lines_assertion, RDFS.label, Literal(f"Assertion about the overall number of verse lines in '{author}: {poem_title}' based on digital analysis with Rantanplan")))

    # Base of argument (P134_continued): This is experimental
    g.add((overall_number_of_verse_lines_assertion, CRM.P134_continued, clscor_digital_analyis))
    g.add((clscor_digital_analyis, CRM.P134i_was_continued_by, overall_number_of_verse_lines_assertion))

    overall_number_of_verse_lines_dimension = URIRef(generate_clscor_uri(str(create_uri("E45_OVERALL_NUM_OF_LINES", author, poem_title))))
    
    g.add((overall_number_of_verse_lines_dimension, RDF.type, CRM.E54_Dimension))
    g.add((overall_number_of_verse_lines_dimension, RDFS.label, Literal(f"Overall number of verse lines in '{author}: {poem_title}' [Calculated Value]")))
    g.add((overall_number_of_verse_lines_dimension, CRM.P90_has_value, Literal(overall_line_count, datatype=XSD.Integer)))
    
    unit_verse_line = URIRef(generate_clscor_uri("unit/segment/verse_line"))
    g.add((unit_verse_line, RDF.type, CLS.X3_Feature))
    g.add((unit_verse_line, RDFS.label, Literal("Verse Line [Feature: Measurement Unit, Type]")))

    g.add((overall_number_of_verse_lines_dimension, CRM.P91_has_unit, unit_verse_line))
    g.add((unit_verse_line, CRM.P91i_is_unit_of, overall_number_of_verse_lines_dimension))

    g.add((overall_number_of_verse_lines_assertion, CRM.P141_assigned, overall_number_of_verse_lines_dimension))
    g.add((overall_number_of_verse_lines_dimension, CRM.P141i_was_assigned_by, overall_number_of_verse_lines_assertion))

    g.add((overall_number_of_verse_lines_assertion, CRM.P140_assigned_attribute_to, r_redaction))
    g.add((r_redaction, CRM.P140i_was_attributed_by, overall_number_of_verse_lines_assertion))


    # TODO: add the verse line structure as well
    # This is different than the units, maybe assign an identifier?!
    verse_line_structure_vals = map(str, line_counts_in_stanzas)
    verse_line_structure = "-".join(verse_line_structure_vals)
    verse_line_structure_assertion = URIRef(generate_clscor_uri(str(create_uri("E13_VERSE_LINE_STRUCTURE", author, poem_title))))
    
    g.add((verse_line_structure_assertion, RDF.type, CRM.E13_Attribute_Assignment))
    g.add((verse_line_structure_assertion, RDFS.label, Literal(f"Assertion about verse line distribution on stanzas of '{author}: {poem_title}' based on digital analysis with Rantanplan")))

    # Base of argument (P134_continued): This is experimental
    g.add((verse_line_structure_assertion, CRM.P134_continued, clscor_digital_analyis))
    g.add((clscor_digital_analyis, CRM.P134i_was_continued_by, verse_line_structure_assertion))

    # This is not ideal because there is no good way to attach the actual value
    verse_line_distribution_type = URIRef(generate_clscor_uri(f"postdata/type/verse_line_distribution/{verse_line_structure}"))
    g.add((verse_line_distribution_type, RDF.type, CRM.E55_Type))
    g.add((verse_line_distribution_type, RDFS.label, Literal(f"Verse Line Distribution: {verse_line_structure}")))
    g.add((verse_line_distribution_type, CRM.P3_has_note, Literal(verse_line_structure)))

    g.add((verse_line_structure_assertion, CRM.P141_assigned, verse_line_distribution_type))
    g.add((verse_line_distribution_type, CRM.P141i_was_assigned_by, verse_line_structure_assertion))

    return graph_name


def join_lines(stanza):
    stanza_content = []
    for line in stanza:
        line_text = join_tokens(line["tokens"])
        stanza_content.append(line_text)
    return "\n".join(stanza_content)


def join_tokens(tokens):
    """Join all words from a list of tokens into a string.

    :param tokens: List of dictionaries representing tokens
    :return: String of words
    """
    output = []
    for token in tokens:
        item = join_syllables(token)
        output.append(item)
    return " ".join(output)


def join_syllables(token):
    """Join all symbols and syllables from a list of tokens into a string.

    :param token: List of dictionaries representing tokens
    :return: String of syllables
    """
    if "symbol" in token:
        return token["symbol"]
    else:
        return "".join([syll["syllable"] for syll in token["word"]])


def get_grammatical_stress_pattern(tokens):
    stresses = []
    for token in tokens:
        word = token.get("word")
        if word:
            for syllable in word:
                stresses.append(syllable["is_stressed"])
    return format_stress(stresses, "pattern")


def get_rhyme_pattern(stanza):
    return "".join(line["rhyme"] for line in stanza)


def get_rhymes_lines(stanza):
    rhymes_dict = {}
    for idx, line in enumerate(stanza):
        if line["rhyme"] != "-":
            if rhymes_dict.get(line["rhyme"]):
                rhymes_dict[line["rhyme"]].append(idx)
            else:
                rhymes_dict[line["rhyme"]] = [idx]
    return rhymes_dict


def get_last_word_index(tokens):
    last_word_index = -1
    for token in tokens[::-1]:
        if "word" in token:
            break
        last_word_index -= 1
    return tokens.index(tokens[last_word_index])


def include_dieresis(tokens, phnological_groups):
    met_syll_count = 0
    synalepha_counter = 0
    print(tokens)
    print(phnological_groups)
    for token in tokens:
        if "word" in token:
            word = token["word"]
            for gram_syll in word:
                print(gram_syll, met_syll_count)
                if synalepha_counter > 0:
                    synalepha_counter = synalepha_counter - 1
                    continue
                if "synalepha_index" in phnological_groups[met_syll_count]:
                    synalepha_counter = len(
                        phnological_groups[met_syll_count]["synalepha_index"])
                    continue
                if "sinaeresis_index" in phnological_groups[met_syll_count]:
                    continue
                if met_syll_count < len(phnological_groups) - 1:
                    if (gram_syll["syllable"] !=
                      phnological_groups[met_syll_count]["syllable"]) \
                    and (gram_syll["syllable"] ==
                         (phnological_groups[met_syll_count]["syllable"]
                          + phnological_groups[met_syll_count+1]["syllable"])):
                        dieresis_index = len(phnological_groups[met_syll_count]["syllable"]) - 1
                        gram_syll.update({"has_dieresis": True,
                                          "dieresis_index": dieresis_index})
                        met_syll_count = met_syll_count + 1
                        continue
                met_syll_count = met_syll_count + 1
    return tokens
