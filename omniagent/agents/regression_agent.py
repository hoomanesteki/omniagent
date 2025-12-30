"""
Regression Agent - Predictive modeling tools.

Provides tools for:
- Linear regression
- Model diagnostics
- Predictions
"""

from typing import Any

from omniagent.agents.base import BaseAgent
from omniagent.mcp.server import mcp_tool


class RegressionAgent(BaseAgent):
    """
    Agent for regression modeling.
    
    Tools:
    - fit: Fit a regression model
    - predict: Make predictions
    - diagnostics: Model diagnostics
    """
    
    name = "regression_agent"
    description = "Fits regression models and makes predictions"
    
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._models: dict[str, Any] = {}
        self._model_counter = 0
    
    @mcp_tool
    def fit(
        self,
        target: str,
        features: list[str],
        model_type: str = "linear",
        test_size: float = 0.2,
    ) -> dict[str, Any]:
        """
        Fit a regression model.
        
        Args:
            target: Target column to predict
            features: List of feature columns
            model_type: Type of model - 'linear' or 'ridge'
            test_size: Fraction of data to use for testing (0.0 to 0.5)
            
        Returns:
            Dictionary with model metrics, coefficients, and model ID
        """
        try:
            import numpy as np
            from sklearn.linear_model import LinearRegression, Ridge
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
        except ImportError:
            return {"error": "scikit-learn not installed. Run: pip install scikit-learn"}
        
        table_name = self._get_table_name()
        
        # Validate columns
        all_columns = [target] + features
        valid, error = self._validate_columns(table_name, all_columns)
        if not valid:
            return {"error": error}
        
        # Check columns are numeric
        numeric_cols = self._get_numeric_columns(table_name)
        non_numeric = [c for c in all_columns if c not in numeric_cols]
        if non_numeric:
            return {"error": f"Non-numeric columns: {', '.join(non_numeric)}"}
        
        # Clamp test_size
        test_size = max(0.1, min(0.5, test_size))
        
        # Fetch data
        columns_sql = ", ".join(f'"{c}"' for c in all_columns)
        result = self.db.connection.execute(f"""
            SELECT {columns_sql}
            FROM {table_name}
            WHERE {" AND ".join(f'"{c}" IS NOT NULL' for c in all_columns)}
        """)
        data = result.fetchall()
        
        if len(data) < 10:
            return {"error": f"Insufficient data: only {len(data)} complete rows"}
        
        # Convert to arrays
        data_array = np.array(data, dtype=np.float64)
        y = data_array[:, 0]  # target is first column
        X = data_array[:, 1:]  # features are rest
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Create model
        if model_type == "ridge":
            model = Ridge(alpha=1.0)
        else:
            model = LinearRegression()
        
        # Fit model
        model.fit(X_train, y_train)
        
        # Predictions
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        
        # Metrics
        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)
        test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
        test_mae = mean_absolute_error(y_test, y_test_pred)
        
        # Coefficients
        coefficients = {
            feat: round(coef, 6)
            for feat, coef in zip(features, model.coef_)
        }
        
        # Store model
        self._model_counter += 1
        model_id = f"model_{self._model_counter}"
        self._models[model_id] = {
            "model": model,
            "features": features,
            "target": target,
            "model_type": model_type,
        }
        
        return {
            "model_id": model_id,
            "model_type": model_type,
            "target": target,
            "features": features,
            "metrics": {
                "train_r2": round(train_r2, 4),
                "test_r2": round(test_r2, 4),
                "test_rmse": round(test_rmse, 4),
                "test_mae": round(test_mae, 4),
            },
            "coefficients": coefficients,
            "intercept": round(float(model.intercept_), 6),
            "sample_size": {
                "train": len(X_train),
                "test": len(X_test),
                "total": len(data),
            },
        }
    
    @mcp_tool
    def predict(
        self,
        model_id: str,
        values: dict[str, float],
    ) -> dict[str, Any]:
        """
        Make a prediction using a fitted model.
        
        Args:
            model_id: ID of the fitted model
            values: Dictionary of feature values
            
        Returns:
            Dictionary with prediction
        """
        try:
            import numpy as np
        except ImportError:
            return {"error": "numpy not installed"}
        
        if model_id not in self._models:
            return {"error": f"Model not found: {model_id}. Available: {list(self._models.keys())}"}
        
        model_info = self._models[model_id]
        model = model_info["model"]
        features = model_info["features"]
        
        # Check all features provided
        missing = [f for f in features if f not in values]
        if missing:
            return {"error": f"Missing features: {', '.join(missing)}"}
        
        # Create input array
        X = np.array([[values[f] for f in features]])
        
        # Predict
        prediction = model.predict(X)[0]
        
        return {
            "model_id": model_id,
            "input": values,
            "prediction": round(float(prediction), 4),
            "target": model_info["target"],
        }
    
    @mcp_tool
    def diagnostics(
        self,
        model_id: str,
    ) -> dict[str, Any]:
        """
        Get detailed diagnostics for a fitted model.
        
        Args:
            model_id: ID of the fitted model
            
        Returns:
            Dictionary with diagnostic information
        """
        try:
            import numpy as np
        except ImportError:
            return {"error": "numpy not installed"}
        
        if model_id not in self._models:
            return {"error": f"Model not found: {model_id}"}
        
        model_info = self._models[model_id]
        model = model_info["model"]
        features = model_info["features"]
        target = model_info["target"]
        
        # Fetch all data to compute residuals
        table_name = self._get_table_name()
        all_columns = [target] + features
        columns_sql = ", ".join(f'"{c}"' for c in all_columns)
        
        result = self.db.connection.execute(f"""
            SELECT {columns_sql}
            FROM {table_name}
            WHERE {" AND ".join(f'"{c}" IS NOT NULL' for c in all_columns)}
        """)
        data = np.array(result.fetchall(), dtype=np.float64)
        
        y = data[:, 0]
        X = data[:, 1:]
        
        # Predictions and residuals
        y_pred = model.predict(X)
        residuals = y - y_pred
        
        # Residual statistics
        residual_stats = {
            "mean": round(float(np.mean(residuals)), 6),
            "std": round(float(np.std(residuals)), 4),
            "min": round(float(np.min(residuals)), 4),
            "max": round(float(np.max(residuals)), 4),
            "median": round(float(np.median(residuals)), 4),
        }
        
        # Feature importance (absolute coefficients)
        coef_importance = sorted(
            [
                {"feature": feat, "coefficient": round(float(coef), 6), "abs_importance": round(float(abs(coef)), 6)}
                for feat, coef in zip(features, model.coef_)
            ],
            key=lambda x: x["abs_importance"],
            reverse=True,
        )
        
        return {
            "model_id": model_id,
            "residual_statistics": residual_stats,
            "feature_importance": coef_importance,
            "sample_residuals": [round(float(r), 4) for r in residuals[:20].tolist()],
        }
    
    @mcp_tool
    def list_models(self) -> dict[str, Any]:
        """
        List all fitted models.
        
        Returns:
            Dictionary with model summaries
        """
        models = []
        for model_id, info in self._models.items():
            models.append({
                "model_id": model_id,
                "model_type": info["model_type"],
                "target": info["target"],
                "features": info["features"],
            })
        
        return {
            "model_count": len(models),
            "models": models,
        }
