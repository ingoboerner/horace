import os
from core import add_core_elements
from poetic import add_metrical_elements, add_rantanplan_elements
from rantanplan import get_scansion
from jollyjumper import get_enjambment
import json
import sys
import getopt
from pyld import jsonld
from utils import CONTEXT, QUERY
from rdflib import Graph, ConjunctiveGraph
from clscor import generate_corpus_rdf 


def generate(corpora_root, rdf_root, scansions_root):
    total_jsons = {}
    # base_root = "/home/uned/POSTDATA/corpora/"
    base_root = corpora_root
    datasets = os.listdir(base_root)
    print(datasets)

    # corpora that can be added (IB)
    spanish_datasets = ["disco2_1", "disco3", "adso", "adso100", "plc", "gongo"]
    all_datasets = spanish_datasets + ["fbfv", "ecpa"]
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

    # Don't know what fbfv is, need to check if it get's loaded at all... (IB)

    for dataset in datasets:
        if dataset in all_datasets:
            print(dataset)
            # maybe could call a function to create rdf of corpus here? (IB)
            # This is added for CLSCor
            corpus_uri = generate_corpus_rdf(dataset)
            print(f"Generated corpus.ttl. Corpus URI is {corpus_uri}")
            jsons_root = base_root + dataset + "/averell/parser"
            authors = os.listdir(jsons_root)
            print(authors)
            for author in [a for a in authors if os.path.isdir(jsons_root + "/" + a)]:
                json_files = os.listdir(jsons_root + "/" + author)
                for json_file in json_files:
                    if json_file[-5:] == ".json":
                        total_jsons.update({json_file[:-5]: jsons_root + "/" + author + "/" + json_file})

    n_doc = 0
    for name, root in total_jsons.items():
        rdf = ConjunctiveGraph()
        n_doc += 1

        _json = json.load(open(root))

        # rdf = add_core_elements(rdf, _json)
        add_core_elements(rdf.store, _json)
        length = 0
        for quad in rdf.quads():
            length += 1
        print("LEN1", length)
        for con in rdf.contexts():
            print("CON1", con)

        # this seems to add the manual annotations (could remove them here?)
        if scansions_root is not None:
            scansion_graph_uri = add_metrical_elements(rdf.store, _json, n_doc)
        else:
            scansion_graph_uri = add_metrical_elements(rdf.store, _json, None)

        # rdf = metrical_elements
        length = 0
        for quad in rdf.quads():
            length += 1
        print("LEN2", length)

        for con in rdf.contexts():
            print("CON2", con)

        poem_text = "\n\n".join([stanza["stanza_text"] for stanza in _json["stanzas"]])
        poem_title = _json["poem_title"]
        author = _json["author"]
        dataset = _json["corpus"]

        if dataset in spanish_datasets:
            scansion = None
            enjambments = None
            try:
                scansion = get_scansion(poem_text, rhyme_analysis=True, rhythm_format="pattern",
                     rhythmical_lengths=None, split_stanzas_on=r"\n\n",
                     pos_output=False, always_return_rhyme=True)
                # print(scansion)
            except:
                print("Rantanplan Error", " -- ", poem_title, "--", author, "--", dataset)
                pass
            try:
                enjambments = get_enjambment(poem_text)
                # print(enjambments)
            except:
                print("JollyJumper Error")
                pass

            if scansion is not None:
                # try:
                    if scansions_root is not None:
                        scansion_graph_uri = add_rantanplan_elements(rdf.store, scansion, poem_title, author, dataset, enjambments, n_doc)

                    else:
                        scansion_graph_uri = add_rantanplan_elements(rdf.store, poem_title, author, dataset, enjambments, None)

                # except:
                    # print("Horace error parsing ", poem_title, "--", author, "--", dataset)
                    # raise
                    # pass
                # print("PARSED", " -- ", poem_title, "--", author,
        length = 0
        for quad in rdf.quads():
            length += 1
        print("LEN3", length)

        for con in rdf.contexts():
            print("CON3", con)

        rdf.serialize(rdf_root + "poem_" + str(n_doc) + ".ttl",
                      format="ttl", encoding="utf-8")
        if n_doc % 300 == 0:
            print("PARSED TO RDF #", n_doc, "--- Last poem -> ", name, root)


def transform_json_ld(json_ld):
    """Returns a json_ld compacted and framed representation of the initial
    json_ld"""
    json_ld_result = json.loads(json_ld)
    framed = jsonld.frame(json_ld_result, json.loads("""{
	"http://postdata.linhd.uned.es/ontology/postdata-poeticAnalysis#stanzaList": {
		"@embed": "@always",
		"http://postdata.linhd.uned.es/ontology/postdata-poeticAnalysis#lineList": {
			"@embed": "@always"
		}
	}
}"""))
    with open('json.json', 'w') as outfile:
        json.dump(json_ld_result, outfile)
    # framed = jsonld.frame(json_ld_result, {})
    # print(json.dumps(framed, indent=2))
    compacted = jsonld.compact(framed, CONTEXT)
    # graph = compacted.get("@graph")
    del compacted["@context"]
    # ordered = sort_jsonld(compacted)
    # return ordered
    return compacted


def sort_jsonld(jsonld):
    if "stanzaList" in jsonld:
        jsonld["stanzaList"] = sorted(jsonld["stanzaList"], key=lambda x: x["stanzaNumber"], reverse=False)
        for stanza in jsonld["stanzaList"]:
            if "lineList" in stanza.keys():
                stanza["lineList"] = sorted(stanza["lineList"], key=lambda x: x["relativeLineNumber"], reverse=False)
                for line in stanza["lineList"]:
                    if "metricalSyllableList" in line.keys():
                        line["metricalSyllableList"] = sorted(line["metricalSyllableList"], key=lambda x: x["metricalSyllableNumber"], reverse=False)
                    if "wordList" in line.keys():
                        print(line["wordList"])
                        line["wordList"] = sorted(line["wordList"], key=lambda x: x["wordNumber"], reverse=False)
                        for word in line:
                            if "isWordAnalysedBy" in line:
                                word["isWordAnalysedBy"] = sorted(word["isWordAnalysedBy"], key=lambda x: x["grammaticalSyllableNumber"], reverse=False)
    return jsonld


def query():
    """Not used"""
    import requests
    from requests.auth import HTTPBasicAuth

    sparql_endpoint = "http://localhost:3030/core_dataset/sparql"
    sparqlquery = "SELECT DISTINCT ?a WHERE { ?a ?b ?c. }"

    params = {
        "query": sparqlquery
    }
    headers = {
        'Accept': 'application/sparql-results+json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:59.0) Gecko/20100101 Firefox/59.0'
    }
    get = requests.get(sparql_endpoint, params=params, headers=headers)
    results = get.content
    print(results)


def main(argv):
    inputfolder = ''
    # The input folder that has as subfolders for each dataset downloaded by averell
    # "/home/uned/POSTDATA/corpora/"
    outputfolder = ''
    # "/home/uned/POSTDATA/KG/"
    scansionfolder = ''
    # "home/uned/POSTDATA/SCANSIONS"
    try:
        opts, args = getopt.getopt(argv, "i:o:s:", ["ifold=", "ofold=", "sfold="])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-i", "--ifold"):
            inputfolder = arg
        elif opt in ("-o", "--ofold"):
            outputfolder = arg
        elif opt in ("-s", "--sfold"):
            scansionfolder = arg

    print("EXECUTE ARGS : ", inputfolder, outputfolder, scansionfolder)
    generate(inputfolder, outputfolder, scansionfolder)


if __name__ == "__main__":
    main(sys.argv[1:])
    # generate("/home/uned/POSTDATA/corpora/", "/home/uned/POSTDATA/KG/")
