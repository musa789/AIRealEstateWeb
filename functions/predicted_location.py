import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import folium
from flask import Flask, request, jsonify
import tempfile

app = Flask(__name__)

def filter_data(data, budget, city, property_type):
    filtered_data = data.loc[(data['city'] == city) & (data['property_type'] == property_type) & (data['price'] <= budget)]
    return filtered_data


def predict_price(filtered_data, period):
    features = ['beds', 'baths']
    X = filtered_data[features]
    y = filtered_data['price']

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    predicted_price = model.predict([[3, 2], [4, 3], [3, 2], [4, 3]])
    predicted_price_period = predicted_price[int(period)-1]

    return predicted_price_period


@app.route('/', methods=['POST'])
def predict_location():
    # Load data
    data = pd.read_csv('zameen_data.csv')

    # Get input from request
    budget = int(request.json['budget'])
    city = request.json['city']
    property_type = request.json['property_type']
    period = request.json['period']

    filtered_data = filter_data(data, budget, city, property_type)
    predicted_price_period = predict_price(filtered_data, period)

    # Create map centered on the first property in filtered_data
    center_lat = filtered_data.iloc[0]['latitude']
    center_lon = filtered_data.iloc[0]['longitude']
    map_location = [center_lat, center_lon]
    m = folium.Map(location=map_location, zoom_start=15)

    # Add markers to the map for each property in filtered_data
    for index, row in filtered_data.iterrows():
        price = row['price']
        lat = row['latitude']
        lon = row['longitude']
        tooltip = f"Price: {price} PKR"
        folium.Marker([lat, lon], tooltip=tooltip).add_to(m)

    # Add marker for predicted location
    predicted_lat = filtered_data.iloc[0]['latitude'] + 0.001
    predicted_lon = filtered_data.iloc[0]['longitude'] + 0.001
    predicted_tooltip = f"Predicted Price: {predicted_price_period:.2f} PKR"
    folium.Marker([predicted_lat, predicted_lon], tooltip=predicted_tooltip, icon=folium.Icon(color='green')).add_to(m)

    # Save map to temporary HTML file
    temp_file = tempfile.NamedTemporaryFile(suffix='.html', delete=False)
    temp_file.close()
    m.save(temp_file.name)

    # Return predicted price and map as JSON response
    response = {
        'predicted_price': predicted_price_period,
        'map_url': 'file://' + temp_file.name
    }
    return jsonify(response)


if __name__ == "__main__":
    app.run()
