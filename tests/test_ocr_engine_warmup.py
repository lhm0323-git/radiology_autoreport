from ocr_engine import bmd_warm_up_shapes


def test_bmd_warm_up_shapes_match_configured_roi_sizes():
    config = {
        "roi_bmd": {
            "patient_info": {"width_pct": 0.2624, "height_pct": 0.1899},
            "results": {"width_pct": 0.6816, "height_pct": 0.2495},
        }
    }

    assert bmd_warm_up_shapes(config, (1920, 1080)) == [
        (205, 503),
        (269, 1308),
    ]