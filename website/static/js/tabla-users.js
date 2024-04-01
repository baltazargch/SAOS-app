// Configuración de DataTables
$(document).ready(function () {
  // Inicializar DataTables
  var table = $("#tabla-users").DataTable({
    // Configuración de paginación
    paging: true,
    pageLength: 6, // Número de filas por página
    lengthChange: false, // Ocultar selector de cantidad de filas por página
    searching: false, // Ocultar barra de búsqueda
    info: false, // Ocultar información de la tabla
    ordering: false, // Desactivar ordenamiento de columnas
  });

  // Inicializar DataTables
  var table = $("#tabla-permits").DataTable({
    // Configuración de paginación
    paging: true,
    pageLength: 10, // Número de filas por página
    lengthChange: false, // Ocultar selector de cantidad de filas por página
    searching: false, // Ocultar barra de búsqueda
    info: false, // Ocultar información de la tabla
    ordering: false, // Desactivar ordenamiento de columnas
  });
});
