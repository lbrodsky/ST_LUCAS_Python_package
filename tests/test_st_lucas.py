#!/usr/bin/env python3

import sys
import os
import pytest
import tempfile
from pathlib import Path

from osgeo import gdal
from owslib.fes import PropertyIsEqualTo

sys.path.insert(0, str(Path(__file__).parent.parent))
from st_lucas import LucasIO, LucasRequest, __version__
from st_lucas.exceptions import LucasDownloadError

class TestST_LUCAS:
    num_of_features = 1
    point_id = 28382290
    
    def _request(self, st=True):
        request = LucasRequest()
        request.operator=PropertyIsEqualTo
        request.propertyname = 'point_id'
        request.literal = str(self.point_id)
        request.st_aggregated = st

        return request

    def _download(self, st=True):
        request = self._request(st)
        lucasio = LucasIO()
        lucasio.download(request)
        return lucasio
    
    def test_001(self):
        """Build a request.

        This tests case consists of checking that LucasRequest.build()
        returns request based on specified filters.
        """
        data = self._request().build()
        
        assert data['typename'] == 'lucas:lucas_st_points'
        assert data['filter'] == f'<ogc:PropertyIsEqualTo xmlns:ogc="http://www.opengis.net/ogc"><ogc:PropertyName>point_id</ogc:PropertyName><ogc:Literal>{self.point_id}</ogc:Literal></ogc:PropertyIsEqualTo>'
    
    def test_002(self):
        """Download LUCAS subset based on request.

        This tests case consists of checking that LucasIO.download()
        retrieves expected LUCAS subset from remote server.
        """
        assert self._download().count() == self.num_of_features

    def test_003(self):
        """Identify LUCAS metadata.

        This tests case consists of checking that LucasIO.metadata
        returns expected LUCAS metadata directory.
        """
        md = self._download().metadata
        
        assert md["LUCAS_TABLE"] == "lucas_st_points"
        assert md["LUCAS_ST"] == "1"
        assert md["LUCAS_CLIENT_VERSION"] == str(__version__)
        assert float(md["LUCAS_DB_VERSION"]) >= 0.9
        assert int(md["LUCAS_MAX_FEATURES"]) > 0

    def test_004(self):
        """Save LUCAS subset to GeoPackage format.

        This tests case consists of checking that created GeoPackage file
        can be open by GDAL library and contains expected number of
        features.
        """
        gpkg_file = Path(tempfile.gettempdir()) / Path(str(os.getpid()) + '.gpkg')
        self._download().to_gpkg(gpkg_file)
        ds = gdal.OpenEx(str(gpkg_file), gdal.OF_VECTOR | gdal.OF_READONLY)
        assert ds.GetLayer().GetFeatureCount() == self.num_of_features
        del ds

    def test_005(self):
        """Identify photos for LUCAS point/year.

        This tests case consists of checking that LucasIO.get_images()
        returns expected directory of images.
        """
        images = self._download(st=False).get_images(2018, self.point_id)

        assert len(images.keys()) == 5

    def test_006(self):
        """Identify empty subset.

        This tests case consists of checking that is_empty() method
        works as expected on empty subset.
        """
        req = LucasRequest()
        req.bbox = (0, 0, 1, 1)
        lucasio = LucasIO()
        lucasio.download(req)

        assert lucasio.count() == 0
        assert lucasio.is_empty() is True

    def test_007(self):
        """Identify max feature property.

        This tests case consists of checking that MAX_FEATURES
        property.
        """
        req = LucasRequest()
        req.bbox = (3764067 ,2361825, 5030245, 3685331)
        lucasio = LucasIO()
        lucasio.download(req)

        assert lucasio.count() == int(lucasio.metadata['LUCAS_MAX_FEATURES'])
