import polars as pl
import polars.testing as pl_testing
# Import the transformer class from your localized script file
from src.transformation.f1_to_silver.f1_to_silver import F1Transformer

def test_transform_results_parses_nested_structures(mock_bronze_results_json):
    """Verifies that nested JSON lists/structs unfold into flattened tables properly."""
    transformer = F1Transformer()
    
    circuits, races, drivers, constructors, race_results = transformer.transform_results(mock_bronze_results_json)
    
    assert isinstance(race_results, pl.DataFrame)
    assert isinstance(races, pl.DataFrame)
    
    assert "raceId" in races.columns
    assert "positionOrder" in race_results.columns
    
    expected_race_id = 202401
    assert races.select("raceId").item(0) == expected_race_id
    assert race_results.select("raceId").item(0) == expected_race_id

def test_dataframe_exact_match_example():
    """Example showing how to assert perfect structural alignment in Polars."""
    df_actual = pl.DataFrame({"id": [1, 2], "val": [10.0, 20.0]})
    df_expected = pl.DataFrame({"id": [1, 2], "val": [10.0, 20.0]})
    
    pl_testing.assert_frame_equal(df_actual, df_expected)