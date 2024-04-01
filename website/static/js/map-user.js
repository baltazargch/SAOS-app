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
    a.id = lugar.properties.Loteo;
    a.href = "#";
    p.innerText = "Lotes disponibles: xx. Lotes vendidos: XX.";
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
    onEachFeature: onEachFeature,
  }).addTo(mapLot);
}

// Usage: Call fetchAndAddGeojsonToMap
fetchAndAddGeojsonToMap();

// open form modal
function openFormModal(e) {
  //TODO: make css code
  let props = e.target.feature.properties;
  UIkit.modal.dialog(
    '<form action="/modify_map" method="POST" class="uk-form-stacked">' +
      '<div class="wrapper-modal-lotes">' +
      '<div class="form-modal-value">' +
      '<div class="uk-modal-body">' +
      "<h3><b>Información del Lote</b></h3>" +
      '<label class="uk-form-label" for="form-stacked-text">Proyecto</label>' +
      '<div class="uk-form-controls"><input class="uk-input" type="text" name="loteo" value="' +
      props.loteo +
      '"></div></br>' +
      '<label class="uk-form-label" for="form-stacked-text">Lote</label>' +
      '<div class="uk-form-controls"><input class="uk-input" type="text" name="parcela" value="' +
      props.nombrecompleto +
      '"></div></br>' +
      '<div class="uk-form-controls"><input class="uk-input" type="text" id="comprador" placeholder="Comprador(es)"></div></br>' +
      '<div class="uk-form-controls"><input class="uk-input" type="date" id="fechareserva"/> </div>' +
      '<div class="uk-margin">' +
      '<select id="estado" class="uk-select" aria-label="Select" name="estado">' +
      "<option>Reservado</option>" +
      "<option>Vendido</option>" +
      "</select>" +
      "</div>" +
      '<div class="uk-container">' +
      '<button class="uk-button uk-button-secondary uk-button-large" type="submit">Enviar</button>' +
      "</div>" +
      "</div>" +
      "</div>" +
      "</div>" +
      "</form>"
  );
  setDateToday();
}

function highlightFeature(e) {
  var layer = e.target;
  layer.setStyle({
    fillOpacity: 0.9,
  });

  layer
    .bindPopup(e.target.feature.properties.nombrecompleto, {
      closeButton: false,
    })
    .openPopup();

  layer.bringToFront();
}

// Reset on no hover
function resetHighlight(e) {
  var layer = e.target;
  layer.setStyle({
    fillOpacity: 0.5,
  });
  layer.closePopup();
}

// use functions on every feature
function onEachFeature(feature, layer) {
  layer.on({
    mouseover: highlightFeature,
    mouseout: resetHighlight,
    click: openFormModal,
  });
}

function setDateToday() {
  // Obtener la fecha de hoy
  var today = new Date();

  // Obtener día, mes y año
  var day = String(today.getDate()).padStart(2, "0");
  var month = String(today.getMonth() + 1).padStart(2, "0"); // El mes se indexa desde 0, por lo que se suma 1
  var year = today.getFullYear();

  // Formatear la fecha en el formato "aaaa-mm-dd"
  var formattedDate = year + "-" + month + "-" + day;

  // Establecer el valor de la fecha formateada en el input
  document.getElementById("fechareserva").value = formattedDate;
}

window.onload = function() {
  var urlParams = new URLSearchParams(window.location.search);
  var loteo = urlParams.get("loteo");
  var clickloteo = urlParams.get("clickloteo");
  // Verificar si se debe realizar la acción
  if (clickloteo === "True") {

    UIkit.notification({message: "<span uk-icon='icon: check'></span> Datos guardados correctamente.", status: 'success', timeout: 1200});
    // Hacer clic en el botón automáticamente
    document.getElementById(loteo).click();


  }
};
  