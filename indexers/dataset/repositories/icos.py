import json
import textwrap

from bs4 import BeautifulSoup
import requests

from .common import Repository
from ..download import TwoStepDownloader
from ..convert import Converter
from ..index import Indexer


class ICOSDownloader(TwoStepDownloader):
    documents_list_url = 'https://meta.icos-cp.eu/sparql'
    document_extension = '.html'

    def get_documents_urls(self):
        sparql_query = r"""
            prefix cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>
            prefix prov: <http://www.w3.org/ns/prov#>
            select ?dobj
            where {
                VALUES ?spec {<http://meta.icos-cp.eu/resources/cpmeta/radonFluxSpatialL3> <http://meta.icos-cp.eu/resources/cpmeta/co2EmissionInventory> <http://meta.icos-cp.eu/resources/cpmeta/sunInducedFluorescence> <http://meta.icos-cp.eu/resources/cpmeta/oceanPco2CarbonFluxMaps> <http://meta.icos-cp.eu/resources/cpmeta/inversionModelingSpatial> <http://meta.icos-cp.eu/resources/cpmeta/biosphereModelingSpatial> <http://meta.icos-cp.eu/resources/cpmeta/ecoFluxesDataObject> <http://meta.icos-cp.eu/resources/cpmeta/ecoEcoDataObject> <http://meta.icos-cp.eu/resources/cpmeta/ecoMeteoDataObject> <http://meta.icos-cp.eu/resources/cpmeta/ecoAirTempMultiLevelsDataObject> <http://meta.icos-cp.eu/resources/cpmeta/ecoProfileMultiLevelsDataObject> <http://meta.icos-cp.eu/resources/cpmeta/atcMeteoL0DataObject> <http://meta.icos-cp.eu/resources/cpmeta/atcLosGatosL0DataObject> <http://meta.icos-cp.eu/resources/cpmeta/atcPicarroL0DataObject> <http://meta.icos-cp.eu/resources/cpmeta/ingosInversionResult> <http://meta.icos-cp.eu/resources/cpmeta/socat_DataObject> <http://meta.icos-cp.eu/resources/cpmeta/etcBioMeteoRawSeriesBin> <http://meta.icos-cp.eu/resources/cpmeta/etcStorageFluxRawSeriesBin> <http://meta.icos-cp.eu/resources/cpmeta/etcBioMeteoRawSeriesCsv> <http://meta.icos-cp.eu/resources/cpmeta/etcStorageFluxRawSeriesCsv> <http://meta.icos-cp.eu/resources/cpmeta/etcSaheatFlagFile> <http://meta.icos-cp.eu/resources/cpmeta/ceptometerMeasurements> <http://meta.icos-cp.eu/resources/cpmeta/globalCarbonBudget> <http://meta.icos-cp.eu/resources/cpmeta/nationalCarbonEmissions> <http://meta.icos-cp.eu/resources/cpmeta/globalMethaneBudget> <http://meta.icos-cp.eu/resources/cpmeta/digHemispherPics> <http://meta.icos-cp.eu/resources/cpmeta/etcEddyFluxRawSeriesCsv> <http://meta.icos-cp.eu/resources/cpmeta/etcEddyFluxRawSeriesBin> <http://meta.icos-cp.eu/resources/cpmeta/atcCh4L2DataObject> <http://meta.icos-cp.eu/resources/cpmeta/atcCoL2DataObject> <http://meta.icos-cp.eu/resources/cpmeta/atcCo2L2DataObject> <http://meta.icos-cp.eu/resources/cpmeta/atcMtoL2DataObject> <http://meta.icos-cp.eu/resources/cpmeta/atcC14L2DataObject> <http://meta.icos-cp.eu/resources/cpmeta/atcMeteoGrowingNrtDataObject> <http://meta.icos-cp.eu/resources/cpmeta/atcCo2NrtGrowingDataObject> <http://meta.icos-cp.eu/resources/cpmeta/atcCh4NrtGrowingDataObject> <http://meta.icos-cp.eu/resources/cpmeta/atcN2oL2DataObject> <http://meta.icos-cp.eu/resources/cpmeta/atcCoNrtGrowingDataObject> <http://meta.icos-cp.eu/resources/cpmeta/atcN2oNrtGrowingDataObject> <http://meta.icos-cp.eu/resources/cpmeta/ingosCh4Release> <http://meta.icos-cp.eu/resources/cpmeta/ingosN2oRelease> <http://meta.icos-cp.eu/resources/cpmeta/atcRnNrtDataObject> <http://meta.icos-cp.eu/resources/cpmeta/drought2018AtmoProduct> <http://meta.icos-cp.eu/resources/cpmeta/modelDataArchive> <http://meta.icos-cp.eu/resources/cpmeta/etcArchiveProduct> <http://meta.icos-cp.eu/resources/cpmeta/dought2018ArchiveProduct> <http://meta.icos-cp.eu/resources/cpmeta/atmoMeasResultsArchive> <http://meta.icos-cp.eu/resources/cpmeta/etcNrtAuxData> <http://meta.icos-cp.eu/resources/cpmeta/etcFluxnetProduct> <http://meta.icos-cp.eu/resources/cpmeta/drought2018FluxnetProduct> <http://meta.icos-cp.eu/resources/cpmeta/etcNrtFluxes> <http://meta.icos-cp.eu/resources/cpmeta/etcNrtMeteosens> <http://meta.icos-cp.eu/resources/cpmeta/etcNrtMeteo> <http://meta.icos-cp.eu/resources/cpmeta/icosOtcL1Product> <http://meta.icos-cp.eu/resources/cpmeta/icosOtcL1Product_v2> <http://meta.icos-cp.eu/resources/cpmeta/icosOtcL2Product> <http://meta.icos-cp.eu/resources/cpmeta/icosOtcFosL2Product> <http://meta.icos-cp.eu/resources/cpmeta/otcL0DataObject> <http://meta.icos-cp.eu/resources/cpmeta/inversionModelingTimeseries>}
                ?dobj cpmeta:hasObjectSpec ?spec .
                FILTER NOT EXISTS {[] cpmeta:isNextVersionOf ?dobj}
            }
            """
        sparql_query = textwrap.dedent(sparql_query).strip()

        r = requests.post(
            self.documents_list_url,
            headers={
                'Cache-Control': 'no-cache',
                'accept': 'text/csv'},
            data={'query': sparql_query},
            )
        return r.text.splitlines()[1:]


class ICOSConverter(Converter):
    contextual_text_fields = ["keywords", "genre", "theme", "name"]
    contextual_text_fallback_field = "Abstract"
    RI = 'ICOS'

    def convert_record(self, raw_filename, converted_filename, metadata):
        with open(raw_filename, 'rb') as f:
            soup = BeautifulSoup(f, 'lxml')

        script = soup.find('script', attrs={'type': 'application/ld+json'})
        raw_doc = json.loads(script.text)

        converted_doc = {
            'ResearchInfrastructure': self.get_RI(raw_doc),
            'url': metadata['url'],
            'acquireLicensePage': raw_doc['acquireLicensePage'],
            'contact': raw_doc['name'],
            'contentInfo': raw_doc['name'],
            'creator': self._extract_creator(raw_doc),
            'datePublished': raw_doc['datePublished'],
            'description': raw_doc['description'],
            'distribution': self._extract_distributionInfo(raw_doc),
            'distributionInfo': self._extract_distributionInfo(raw_doc),
            'identifier': raw_doc['identifier'],
            'keywords': raw_doc['keywords'],
            'language': [lang['name'] for lang in raw_doc['inLanguage']],
            'license': raw_doc['license'],
            'modificationDate': raw_doc['dateModified'],
            'name': raw_doc['name'],
            'publisher': raw_doc['publisher']['name'],
            'spatialCoverage': self._extract_spatialCoverage(raw_doc),
            'temporalCoverage': raw_doc['temporalCoverage'],
            'abstract': '',
            }

        self.language_extraction(raw_doc, converted_doc)
        self.post_process_doc(converted_doc)
        self.save_index_record(converted_doc, converted_filename)

    @staticmethod
    def _extract_spatialCoverage(doc):
        coverage = doc['spatialCoverage']
        if isinstance(coverage, list):
            coverage = coverage[0]
        if coverage.get('containedInPlace'):
            coverage = coverage.get('containedInPlace')
        return coverage.get('name')

    @staticmethod
    def _extract_distributionInfo(doc):
        distribution = doc.get('distribution')
        if distribution:
            return distribution.get('contentUrl')

    @staticmethod
    def _extract_creator(doc):
        if isinstance(doc['creator'], dict):
            return [doc['creator']['name']]
        else:
            return [c['name'] for c in doc['creator']]


class ICOSRepository(Repository):
    name = 'ICOS'

    downloader = ICOSDownloader
    converter = ICOSConverter
    indexer = Indexer
