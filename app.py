from flask import Flask, render_template, url_for, request, current_app
from flask_bootstrap import Bootstrap
import folium
import time
import pandas as pd
import matplotlib.pyplot as plt
import folium
import datetime
import json
from folium.plugins import HeatMap
from folium.plugins import HeatMapWithTime

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.df = None


@app.route('/')
def index():
    start_coords = (-34.615267,-58.46461)
    folium_map = folium.Map(location=start_coords, zoom_start=13)
    marker = folium.Marker(location=[-34.622749,-58.4744927])
    folium_map.add_child(marker)
    folium_map.save('static/map.html')
    return render_template('mapa.html', current_time=int(time.time()))

@app.route('/map', methods=['GET', 'POST'])
def mapLatLon():
    marker = None
    latitude = None
    longitude = None

    if request.method == 'POST':
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        marker = folium.Marker(location=[latitude, longitude])
    
    #Create the map
    start_coords = (-34.615267,-58.46461)
    folium_map = folium.Map(location=start_coords, zoom_start=13)

    #Add marker
    if marker is not None:
        folium_map.add_child(marker)

    #Save in html
    folium_map.save('static/map.html')
    return render_template('mapa.html', current_time=int(time.time()), latitude=latitude, longitude=longitude)

@app.route('/heapmap', methods=['GET', 'POST'])
def heapMapLatLon():
    marker = None
    latitude = None
    longitude = None
    dateRequest = None

    if request.method == 'POST':
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        marker = folium.Marker(location=[latitude, longitude], popup='<i>Usted esta aqui!!</i>', tooltip='Click me!', icon=folium.Icon(color='red'))
        dateRequest = request.form.get('date')
        dateform = datetime.datetime.strptime(dateRequest, '%m/%d/%Y')
        dateUse = '2018-' + str(dateform.date().month) + '-' + str(dateform.date().day)
    
    #Create the map
    start_coords = (-34.60, -58.42)
    folium_map = folium.Map(location=start_coords, zoom_start=13)
    folium_map.add_child(folium.LatLngPopup())

    if(dateRequest is not None):
        # Seleccionamos solo las columnas de coordenadas validas para la fecha seleccionada
        df = initDataFrame()
        df_selected = df[(df['latitud'] != 0) & (df['longitud'] != 0) & (df['fecha_for'] == dateUse)  ]

        #Create de HeatMap
        HeatMap(data=df_selected[['latitud', 'longitud', 'count']].groupby(['latitud', 'longitud']).sum().reset_index().values.tolist(), radius=8, max_zoom=13).add_to(folium_map)

        #Add marker
        if marker is not None:
            folium_map.add_child(marker)

        #Save in html
        folium_map.save('static/map.html')
        return render_template('mapa.html', current_time=int(time.time()), latitude=latitude, longitude=longitude, date=dateRequest)
    else:
        #Save in html
        folium_map.save('static/map.html')
        return render_template('mapa.html', current_time=int(time.time()), latitude=latitude, longitude=longitude, date=dateRequest)


@app.route('/heapmapwithtime', methods=['GET', 'POST'])
def heapMapTime():
    #Create the map
    start_coords = (-34.60, -58.42)
    folium_map = folium.Map(location=start_coords, zoom_start=13)

    # Seleccionamos solo las columnas de coordenadas validas para la fecha seleccionada
    df = initDataFrame()
    # Seleccionamos solo las columnas de coordenadas validas para la fecha seleccionada
    df = df[(df['latitud'] != 0) & (df['longitud'] != 0) & (df['anho'] == 2018) & (df['mes'] <= 3) & (df['solo_hora'] != 99)]

    #Creamos la lista de 24 horas
    df_hour_list = []
    for hour in df.solo_hora.sort_values().unique():
        df_hour_list.append(df.loc[df.solo_hora == hour, ['latitud', 'longitud', 'count']].groupby(['latitud', 'longitud']).sum().reset_index().values.tolist())

    #Creamos y agregamos el heatmap por horas
    HeatMapWithTime(df_hour_list, radius=9, gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1: 'red'}, min_opacity=0.1, max_opacity=0.8, use_local_extrema=True).add_to(folium_map)

    #Save in html
    folium_map.save('static/mapWithTime.html')
    return render_template('mapa2.html', current_time=int(time.time()))

@app.route('/clusterKmeans', methods=['GET', 'POST'])
def clustersKmeans():
    #Cargamos los datos
    geo_json_data = json.load(open('datasets/barrios.geojson'))
    clusters = pd.read_csv('datasets/out_kmeans_CABA.csv')
    clusters.rename( columns={'Unnamed: 0':'barrios'}, inplace=True )

    #Correccion de nombre de barrios
    clusters.at[clusters.index[clusters['barrios'] == 'VILLA GRAL MITRE'], 'barrios'] = 'VILLA GRAL. MITRE'
    clusters.at[clusters.index[clusters['barrios'] == 'COGHLAND'], 'barrios'] = 'COGHLAN'
    clusters.at[clusters.index[clusters['barrios'] == 'MONTSERRAT'], 'barrios'] = 'MONSERRAT'
    clusters.at[clusters.index[clusters['barrios'] == 'LA BOCA'], 'barrios'] = 'BOCA'
    clusters.at[clusters.index[clusters['barrios'] == 'NUÑEZ'], 'barrios'] = 'NUÃ‘EZ'

    #Creamos el mapa de CABA
    m = folium.Map(location=[-34.60, -58.42], zoom_start = 12)

    #Agregamos el Choropleth
    folium.Choropleth(
        geo_data=geo_json_data,
        data=clusters,
        columns=['barrios', 'cluster'],
        key_on='feature.properties.barrio',
        fill_color='RdYlBu',
        fill_opacity=0.6,
        line_opacity=0.2,
        legend_name='Clusters kmeans',
        highlight=True
    ).add_to(m)

    #Save in html
    m.save('static/mapKmean.html')
    return render_template('mapa3.html', current_time=int(time.time()))

def initDataFrame():
    global df
    df = pd.read_csv('datasets/delitos.csv')

    #Borramos las columnas sin datos
    df.drop(['lugar'], axis = 1, inplace=True)
    df.drop(['origen_dato'], axis = 1, inplace=True)

    #Completamos los datos nulos
    df['hora'].fillna('99:99:99', inplace = True)
    df['comuna'].fillna('N/A', inplace = True)
    df['barrio'].fillna('N/A', inplace = True)

    #Damos formato a la fecha
    df['fecha_for'] = pd.to_datetime(df['fecha'])
    #Extraemos dia de la semana
    df['dia_semana'] = df['fecha_for'].dt.dayofweek

    #Creamos  un dataframe indexado por fecha
    df.index = pd.DatetimeIndex(df['fecha_for'])

    #creamos las columnas de anho, mes y dia
    df['anho'] = df['fecha_for'].dt.year 
    df['mes'] = df['fecha_for'].dt.month 
    df['dia'] = df['fecha_for'].dt.day
    df['solo_hora'] = df['hora'].apply(lambda s: int(s.split(':')[0]))

    #Creamos una columna auxiliar
    df['count'] = 1

    return df

if __name__ == "__main__":
    initDataFrame()
    app.run(debug=True) 