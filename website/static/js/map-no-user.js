var geojsonData = { data: null };

// Function to fetch a GEOJSON file
async function fetchGeojson(fileName) {
  try {
    // Make a fetch request to the GEOJSON file
    let response = await fetch(`/static/centroids/${fileName}`);

    // Check if the response is successful (status code 200)
    if (!response.ok) {
      throw new Error("Failed to fetch GEOJSON file");
    }

    // Parse the response as JSON and return it
    geojsonData.data = await response.json();

    mapLoteos();
  } catch (error) {
    console.error("Error fetching GEOJSON file:", error);
    return null;
  }
}

// Usage: Call fetchGeojson with the filename and use the returned promise
fetchGeojson("centroids.geojson").then((data) => {});

var mapLot = L.map("mapLot", {
  maxZoom: 18,
}).setView([-42.9095, -71.3143], 14);

var Esri_WorldImagery = L.tileLayer(
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
  {
    attribution:
      "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
  }
);

Esri_WorldImagery.addTo(mapLot);

var myPlaces = L.geoJSON(geojsonData.data, {
  pointToLayer: function (feature, latlng) {
    return L.marker(latlng);
  },
});

myPlaces.addTo(mapLot);

function mapLoteos() {
  const ul = document.querySelector(".items-loteos");
  geojsonData.data.features.forEach((lugar) => {
    const li = document.createElement("li");
    const div = document.createElement("div");
    const a = document.createElement("a");
    const p = document.createElement("p");

    a.addEventListener("click", () => {
      irLoteo(lugar);
    });

    div.classList.add("item-loteo");
    a.innerText = lugar.properties.Loteo;
    a.href = "#";
    p.innerText = "asdasdad";
    /* lugar.properties.Caracteristicas;  */

    div.appendChild(a);
    div.appendChild(p);
    li.appendChild(div);
    ul.appendChild(li);
  });
}

function irLoteo(lugar) {
  const lat = lugar.geometry.coordinates[1];
  const lng = lugar.geometry.coordinates[0];

  mapLot.flyTo([lat, lng], 17, {
    duration: 2,
  });
}

// List of filenames
const fileNames = [
  "ALTOS DE EPUYEN.geojson",
  "BALCONES-RUTA 71.geojson",
  "BOULEVARES II.geojson",
  "LADERAS DEL DON BOSCO.geojson",
  "MIRADORES DEL CORINTO.geojson",
]; 

// Function to fetch and add GEOJSON files to the Leaflet map
async function fetchAndAddGeojsonToMap() {
  try {
    // Iterate through each filename in the list
    for (let fileName of fileNames) {
      // Make a fetch request to the GEOJSON file
      let response = await fetch(`/static/maps/${fileName}`);

      // Check if the response is successful (status code 200)
      if (!response.ok) {
        console.error(`Failed to fetch GEOJSON file ${fileName}`);
        continue; // Skip to the next file
      }

      // Parse the response as JSON
      let geojsonData = await response.json();

      // Add the GEOJSON data to the Leaflet map
      addGeojsonToMap(geojsonData);
    }
  } catch (error) {
    console.error("Error fetching or adding GEOJSON files:", error);
  }
}

// Function to add GEOJSON data to the Leaflet map
function addGeojsonToMap(geojsonData) {
  // Create a GeoJSON layer and add it to the map
  L.geoJSON(geojsonData, {
    style: function (feature) {
      // Get the value of the property to use for coloring (e.g., feature.properties.colorProperty)
      let colorValue = feature.properties.estado;

      // Define colors based on property values
      let color;
      if (colorValue === "DISPONIBLE") {
        color = "green";
      } else if (colorValue === "RESERVADO") {
        color = "blue";
      } else if (colorValue === "VENDIDO") {
        color = "red";
      } else {
        color = "yellow";
      }

      // Return the style object with the desired color
      return {
        fillColor: color,
        weight: 1,
        opacity: 0.7,
        color: "gray",
        fillOpacity: 0.5,
      };
    },
    onEachFeature: function (feature, layer) {
      // Bind a popup to each feature
      layer.bindPopup(
        "<h4><b>Información del lote:</b></h3>" +
          "<b>Nombre</b>: " +
          feature.properties.nombrecompleto +
          "<br>" +
          "<b>Estado</b>: " +
          feature.properties.estado +
          "<br>" +
          "<b>Área aproximada</b>: " +
          feature.properties.area +
          " m<sup>2</sup><br><br>" +
          "<b>Contacta tu inmobiliaria de confianza:</b> </br>" +
          `<div style="justify-content: center; display: flex;">
            <button class="image-button" style="background-image: url('static/media/logo-ameghino.png')" 
            onclick="openPage('https://ameghino830propiedades.com/')"></button>
     
            <button class="image-button" style="background-image: url('static/media/logo-martinez.png')"
            onclick="openPage('https://martinezinmobiliaria.com.ar/')"></button>
                  
            <button class="image-button"style="background-image: url('static/media/saos-nuevo-negro.svg')"
            onclick="openPage('https://saos.app/')"></button>
      
          </div>`
      );
    },
  }).addTo(mapLot);
};

// Usage: Call fetchAndAddGeojsonToMap
fetchAndAddGeojsonToMap();

function openPage(url) {
  // Open the URL in a new window
  window.open(url, '_blank');
}; 


