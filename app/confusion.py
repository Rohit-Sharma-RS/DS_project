import joblib
import pandas as pd
# Load the model
model = joblib.load(r'D:\data-science-end\app\model.joblib')
test_data = pd.DataFrame({'some_feature': [1]})
try:
    model.predict(test_data)
except Exception as e:
    print(e)
