# -*- coding: utf-8 -*-
"""
Nathan Lo
"""

import pandas as pd
from sklearn import preprocessing
import json
import folium
from branca.colormap import LinearColormap
from branca.element import Template, MacroElement
import seaborn as sns

data = pd.read_csv('~/DS projects/Dog map/NYC_Dog_Licensing_Dataset.csv')

noUnknown = data[data['BreedName'] != 'Unknown'].sort_values(by='RowNumber').reset_index().drop(['index'], axis = 1)

breedZIP = noUnknown[['BreedName', 'ZipCode']]
breedZIP['BreedName'] = breedZIP['BreedName'].str.replace(' Crossbreed', '')
breedZIP['BreedName'] = breedZIP['BreedName'].str.replace('Collie, Border', 'Border Collie')
breedZIP['BreedName'] = breedZIP['BreedName'].str.replace(', Toy', '')
breedZIP['BreedName'] = breedZIP['BreedName'].str.replace(', Standard', '')
breedZIP['BreedName'] = breedZIP['BreedName'].str.replace(', Miniature', '')
breedZIP['BreedName'] = breedZIP['BreedName'].str.replace(' Smooth Coat', '')
breedZIP['BreedName'] = breedZIP['BreedName'].str.replace('Bull Dog, English', 'English Bull Dog')
breedZIP['BreedName'] = breedZIP['BreedName'].str.replace(' Terrier/Pit Bull', '')
breedZIP['BreedName'] = breedZIP['BreedName'].str.replace(' Mix / Pit Bull Mix', '')
breedZIP['BreedName'] = breedZIP['BreedName'].str.replace('German Shepherd Dog', 'German Shepherd')
breedCount = pd.DataFrame(breedZIP.groupby(['BreedName', 'ZipCode'])['BreedName'].count())
breedCount = breedCount.rename(columns = {'BreedName' : 'Count'})
breedCount = breedCount.reset_index()
breedCount = breedCount.rename(columns = {'BreedName' : 'Breed Name', 'ZipCode' : 'ZIP Code', 'Count' :'Count'})
breedCount['ZIP Code'] = breedCount['ZIP Code'].apply(int)
breedCount['ZIP Code'] = breedCount['ZIP Code'].apply(str)

#filter zip code to only have largest count from zip code

mostPopularByZIP = breedCount.sort_values('Count', ascending = False).drop_duplicates(['ZIP Code'])
mostPopularByZIP = mostPopularByZIP.reset_index().drop('index', axis = 1)

mostPopularByZIP['Breed Numeric'] = mostPopularByZIP['Breed Name']

le = preprocessing.LabelEncoder()
le.fit(mostPopularByZIP['Breed Numeric'])
mostPopularByZIP['Breed Numeric'] = pd.Series(le.transform(mostPopularByZIP['Breed Numeric']))

mostPopularByZIP = mostPopularByZIP.sort_values(by = 'Count', ascending = False)
mostPopularByZIP = mostPopularByZIP.drop_duplicates(subset = 'ZIP Code')
mostPopularBreedsByZIP = mostPopularByZIP['Breed Name'].value_counts().reset_index()
mostPopularBreedsByZIP.columns = ['Breed Name', 'Counts']
mostPopularTopFifteen = mostPopularBreedsByZIP.sort_values(['Counts'], ascending = False)[0:15]

sns.set_palette(['#b15928', '#fdbf6f', '#999900', '#ff7f00', '#FFA07A', 
                 '#db7093', '#e31a1c', '#1E90FF', '#a6cee3', '#33a02c',
                 '#1f78b4', '#ffff99', '#98FB98', '#b2df8a', '#006400'])
countPlot = sns.barplot(x='Breed Name', y='Counts',
                        data=mostPopularTopFifteen,
                        order=mostPopularTopFifteen['Breed Name'].tolist())
countPlot.set_xticklabels(countPlot.get_xticklabels(), rotation=40, ha="right")
countFig = countPlot.get_figure()
countFig.savefig(fname='Counts Distribution.png', dpi = 100, quality = 100, bbox_inches='tight')

mostDogsByZIP = data[['ZipCode', 'ZipCode']]
mostDogsByZIP.columns = ['ZIP Code', 'Count Code']
mostDogsByZIP = mostDogsByZIP.dropna()
mostDogsByZIP['ZIP Code'] = mostDogsByZIP['ZIP Code'].apply(int)
mostDogsByZIP['ZIP Code'] = mostDogsByZIP['ZIP Code'].apply(str)
mostDogsByZIP = pd.DataFrame(mostDogsByZIP.groupby(['ZIP Code'])['Count Code'].count())
mostDogsByZIP = mostDogsByZIP.reset_index()
mostDogsByZIP.columns = ['ZIP Code', 'Registered Dogs']

with open('~/DS projects/Dog map/nyczipcodetabulationareas.geojson') as jsonFile:
    geoData = json.load(jsonFile)

tmp = geoData

geozips = []
for i in range(len(tmp['features'])):
    if tmp['features'][i]['properties']['postalCode'] in list(breedCount['ZIP Code'].unique()):
        geozips.append(tmp['features'][i])

new_json = dict.fromkeys(['type', 'features'])
new_json['type'] = 'FeatureCollection'
new_json['features'] = geozips

open('filtered-file.geojson', 'w').write(
    json.dumps(new_json, sort_keys = True, indent = 4, separators = (',', ': '))
    )

def create_map(table, zips, mapped_feature, add_text = ''):
    nyc_geo = r'filtered-file.geojson'
    m = folium.Map(location = [40.7128, -74.0060], zoom_start = 11)
    
    m.choropleth(
            geo_data = nyc_geo,
            fill_opacity = 0.7,
            line_opacity = 0.2,
            data = table, 
            key_on = 'feature.properties.postalCode',
            columns = [zips, mapped_feature],
            threshold_scale = [0, 12, 24, 36, 39, 49],
            fill_color = 'Paired',
            legend_name = (' ').join(mapped_feature.split('_')).title() + ' ' + add_text + ' Across New York City'
            )
    
    folium.LayerControl().add_to(m)
    
    m.save(outfile = mapped_feature + '_map.html')

m = folium.Map(location = [40.7128, -74.0060], zoom_start = 11)

#attach colour codes to dog breeds

colours = pd.DataFrame(mostPopularByZIP['Breed Name'].drop_duplicates()).sort_values(['Breed Name']).reset_index().drop('index', axis = 1)
colours['Colours'] = '#000000'
colourDict = {'Yorkshire Terrier' : '#b15928', 'Shih Tzu' : '#fdbf6f', 'American Pit Bull' : '#999900',
              'Labrador Retriever' : '#ff7f00', 'Chihuahua' : '#FFA07A', 'Poodle' : '#db7093',
              'Maltese' : '#e31a1c', 'Beagle' : '#1E90FF', 'French Bulldog' : '#ffff99', 'German Shepherd' : '#a6cee3',
              'Siberian Husky' : '#33a02c', 'Golden Retriever' : '#1f78b4', 'Pomeranian' : '#ffff99',
              'Cocker Spaniel' : '#98FB98', 'Border Collie' : '#b2df8a', 'Australian Shepherd' : '#006400',
              'Bichon Frise' : '#551A8B', 'Dachshund' : '#9ACD32'}
              
colours['Breed Colour Replace'] = colours['Breed Name']
colours['Breed Colour Replace'] = colours['Breed Colour Replace'].replace(colourDict)
colours['Breed Colour Replace'] = colours['Breed Colour Replace'].replace('^[^#\s].*', '#000000', regex = True)
colours = colours.drop('Colours', axis = 1)

sns.set_palette(['#b15928', '#fdbf6f', '#999900', '#ff7f00', '#FFA07A', 
                 '#db7093', '#e31a1c', '#1E90FF', '#a6cee3', '#33a02c',
                 '#1f78b4', '#ffff99', '#98FB98', '#b2df8a', '#006400'])
                 
colours = colours.reset_index()
colours.columns = ['Breed Numeric', 'Breed Name', 'Colours']

fillColours = colours['Colours'].values.tolist()
colours = colours.merge(mostPopularByZIP, 'left').drop_duplicates(subset = 'Breed Numeric').drop(['Count', 'ZIP Code'], axis = 1)

mostPopularByZIP = mostPopularByZIP.merge(colours, how = 'left')

#add in seaborn summarized plots to map

dictMPBZ = mostPopularByZIP[['Breed Numeric', 'ZIP Code']]
dictMPBZ = dictMPBZ.reset_index()
dictMPBZ['Breed ZIP'] = dictMPBZ[['Breed Numeric', 'ZIP Code']].values.tolist()

color_scale = LinearColormap(fillColours, vmin = dictMPBZ['Breed Numeric'].min(), vmax = dictMPBZ['Breed Numeric'].max())

def get_color(feature):
    for i, r in dictMPBZ.iterrows():
        if feature['properties']['postalCode'] == r['Breed ZIP'][1]:
            return color_scale(r['Breed ZIP'][0])              

folium.GeoJson(
    data='~/DS projects/Dog map/filtered-file.geojson',
    style_function = lambda feature: {
        'fillColor': get_color(feature),
        'fillOpacity': 0.8,
        'color' : 'black',
        'weight' : 1,
        'legend_name' : 'Dog Breeds'
    }
).add_to(m)

template = """
{% macro html(this, kwargs) %}

<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>The Most Popular Dog Breeds in NYC by ZIP Code</title>
  <script src="https://unpkg.com/interactjs@1.3.4/dist/interact.min.js"></script>
  <style>
      .item {
          border: 2px solid grey;
          background-color: rgba(255, 255, 255, 0.8);
          border-radius: 6px;
          padding: 10px;
          position: absolute;
      }
      .one {
          z-index: 9999;
          right: 26.5%;
          bottom: 20px;
      }
      .two {
          z-index: 9998;
          right: 20px;
          bottom: 20px;
          width: 25%;
          height: 40%;
      }
      img {
          height: 90%;
          width: 100%;
          opacity: 0.8;
      }
      .three {
          z-index: 9997;
          right: 20px;
          top: 20px;
          width: 25%;
          height: 55%;
          overflow-wrap: break-word;
          overflow-y: scroll;
      }
      .legend-title {
          text-align: left;
          margin-bottom: 5px;
          font-weight: bold;
          font-size: 90%;
      }
      .legend-scale ul {
          margin: 0;
          margin-bottom: 5px;
          padding: 0;
          float: left;
          list-style: none;
       }
      .legend-scale ul li {
          font-size: 80%;
          list-style: none;
          margin-left: 0;
          line-height: 18px;
          margin-bottom: 2px;
      }
      ul.legend-labels li span {
          display: block;
          float: left;
          height: 16px;
          width: 30px;
          margin-right: 5px;
          margin-left: 0;
          border: 1px solid #999;
      }
       a {
          color: #777;
       }
  </style>
</head>

<body>
    <div class = 'item one draggable'>
        <div class='legend-title'>Legend</div>
        <div class='legend-scale'>
          <ul class='legend-labels'>
            <li><span style='background:#999900;opacity:0.7;'></span>American Pit Bull</li>
            <li><span style='background:#b2df8a;opacity:0.7;'></span>Australian Shepherd</li>
            <li><span style='background:#1E90FF;opacity:0.7;'></span>Beagle</li>
            <li><span style='background:#551A8B;opacity:0.7;'></span>Bichon Frise</li>
            <li><span style='background:#1f78b4;opacity:0.7;'></span>Border Collie</li>
            <li><span style='background:#FFA07A;opacity:0.7;'></span>Chihuahua</li>
            <li><span style='background:#a6cee3;opacity:0.7;'></span>Cocker Spaniel</li>
            <li><span style='background:#9ACD32;opacity:0.7;'></span>Dachshund</li>
            <li><span style='background:#ffff99;opacity:0.7;'></span>French Bulldog</li>
            <li><span style='background:#00FFFF;opacity:0.7;'></span>German Shepherd</li>
            <li><span style='background:#33a02c;opacity:0.7;'></span>Golden Retriever</li>
            <li><span style='background:#ff7f00;opacity:0.7;'></span>Labrador Retriever</li>
            <li><span style='background:#e31a1c;opacity:0.7;'></span>Maltese</li>
            <li><span style='background:#006400;opacity:0.7;'></span>Pomeranian</li>
            <li><span style='background:#db7093;opacity:0.7;'></span>Poodle</li>
            <li><span style='background:#fdbf6f;opacity:0.7;'></span>Shih Tzu</li>
            <li><span style='background:#b15928;opacity:0.7;'></span>Yorkshire Terrier</li>        
          </ul>
        </div>
    </div>
    
    <div class = 'item two draggable'>
        <div class='legend-title'>The Top Fifteen Most Popular Dogs in New York City</div>
        <img src = 'Counts Distribution.png'/>
    </div>
    
    <div class = 'item three draggable'>
        <div class='legend-title'>Preamble</div>
        <p>&nbsp;&nbsp;&nbsp;&nbsp;This is a small data visualization project that I worked on. Now that I live in New York City, I've been feeling more connected to the city.
        Considering the amount of dogs I see on my morning commutes, I wondered which dog breeds are the most popular in the city. Since New York City has an
        Open Data Initiative, I accessed the data, cleaned up the data by considering mixed breed dogs as their initial identifying breed (i.e. 
        Labrador Retriever Mixes would be considered Labrador Retrievers) for ease of counting, organized the data by ZIP code for counting,
        counted the dog breeds per ZIP Code. After these initial steps, I sorted the counts in order of most counts to least, then dropped any duplicate ZIP Code
        values by keeping the first (and therefore, most counted) value.<br></br>
        &nbsp;&nbsp;&nbsp;&nbsp;After sorting through the data, my next step was to represent the data on a map. I looked through various visualization libraries and found folium 
        the most amenable to my needs for mapping out geographic data. Since the API wasn't too difficult to access, this part of the project didn't take too long. However,
        I found adding extra features (such as the bar graph visualization, legend, and this preamble) initially challenging. Luckily, I was able to add the draggable windows feature
        through the interact.js library, and this relieved my initial UI issues.<br></br>
        &nbsp;&nbsp;&nbsp;&nbsp;The bar graph was created with seaborn, which I have experience with. One initial obstacle was that I didn't expect seaborn to export the image
        with a cut off, but this issue was fixed by setting more specific quality parameters in the API.<br></br>
        &nbsp;&nbsp;&nbsp;&nbsp;The legend provided the basis for the draggable container window features on this map. Since folium's GEOJson function doesn't come with a legend, I
        coded the legend in order to address this issue.<br></br>
        &nbsp;&nbsp;&nbsp;&nbsp;Overall, I found this project fairly simple in terms of data organization since NYC Open Data's datasets come in a fairly clean format. Using folium's library
        was a fun experience too since I can get a better idea of which dog breeds are popular in which neighbourhoods. My next steps going forward are to learn other data visualization libraries
        (such as Bokeh) and to work with dirtier data so I can get more experience in data cleaning.<br></br>
        - October 2018
        </p>
    </div>
    
<script>

interact('.draggable')
  .draggable({
    // enable inertial throwing
    inertia: true,
   
    // enable autoScroll
    autoScroll: true,

    // call this function on every dragmove event
    onmove: dragMoveListener,
    // call this function on every dragend event
    onend: function (event) {
      var textEl = event.target.querySelector('p');

      textEl && (textEl.textContent =
        'moved a distance of '
        + (Math.sqrt(Math.pow(event.pageX - event.x0, 2) +
                     Math.pow(event.pageY - event.y0, 2) | 0))
            .toFixed(2) + 'px');
    }
  });

  function dragMoveListener (event) {
    var target = event.target,
        // keep the dragged position in the data-x/data-y attributes
        x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx,
        y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;

    // translate the element
    target.style.webkitTransform =
    target.style.transform =
      'translate(' + x + 'px, ' + y + 'px)';

    // update the posiion attributes
    target.setAttribute('data-x', x);
    target.setAttribute('data-y', y);
  }

  // this is used later in the resizing and gesture demos
  window.dragMoveListener = dragMoveListener;
</script>

</body>
{% endmacro %}"""
macro = MacroElement()
macro._template = Template(template)

m.get_root().add_child(macro)

m.save(outfile='Most Popular Dog Breeds in NYC by ZIP Code.html')
