
document.addEventListener("DOMContentLoaded", function () {
    const userBtn = document.getElementById("userBtn");
    const userMenu = document.getElementById("userMenu");

    if (userBtn && userMenu) {
        userBtn.addEventListener("click", function (event) {
            // Alternar la visibilidad del menú
            userMenu.classList.toggle("d-none");
            event.stopPropagation(); // Evitar que el clic se propague y cierre el menú inmediatamente
        });

        // Ocultar el menú si se hace clic fuera de él
        document.addEventListener("click", function (event) {
            if (!userMenu.contains(event.target) && !userBtn.contains(event.target)) {
                userMenu.classList.add("d-none");
            }
        });
    }
});



function toggleListo(productoId) {
    const checkbox = document.getElementById(`switch-${productoId}`);

    // Si el usuario no es superuser, evitar el cambio
    if (checkbox.disabled) {
        return;
    }

    const estadoListo = checkbox.checked;

    fetch(`/producto/toggle_listo/${productoId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ listo: estadoListo }),
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                alert('Hubo un error al actualizar el estado.');
                checkbox.checked = !estadoListo;  // Revierte el cambio si hay error
            }
        })
        .catch(error => {
            console.error('Error:', error);
            checkbox.checked = !estadoListo;  // Revierte el cambio si hay error
        });
}

function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue;
}

function ordenarPor(campo) {
    const urlParams = new URLSearchParams(window.location.search);
    const ordenActual = urlParams.get('orden') === 'asc' ? 'desc' : 'asc';
    urlParams.set('orden', ordenActual);
    urlParams.set('ordenar_por', campo);
    window.location.search = urlParams.toString();
}

function seleccionarEstrella(valor) {
    document.getElementById('estrella' + valor).checked = true;
}

const editarProductoModal = document.getElementById('editarProductoModal');
editarProductoModal.addEventListener('show.bs.modal', function (event) {
    const button = event.relatedTarget;
    const id = button.getAttribute('data-id');
    const sku = button.getAttribute('data-sku');
    const descripcion = button.getAttribute('data-descripcion');
    const precio = button.getAttribute('data-precio');
    const importancia = button.getAttribute('data-importancia');


    const modalForm = editarProductoModal.querySelector('form');
    modalForm.action = `/producto/actualizar/${id}/`;
    document.getElementById('editarId').value = id;
    document.getElementById('editarSku').value = sku;
    document.getElementById('editarDescripcion').value = descripcion;
    document.getElementById('editarPrecioCompra').value = precio;


    if (importancia) {
        const importanciaInput = document.getElementById(`editarEstrella${importancia}`);
        if (importanciaInput) importanciaInput.checked = true;
    }
});

function eliminarProducto(productoId) {
    if (!confirm("¿Estás seguro de que deseas eliminar este producto?")) {
        return;
    }

    fetch(`/producto/eliminar/${productoId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}',
            'Content-Type': 'application/json',
        },
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                location.reload();
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error al eliminar el producto:', error);
            alert('Ocurrió un error al intentar eliminar el producto.');
        });
}

document.addEventListener("DOMContentLoaded", () => {
    const messages = document.querySelector('.alert');
    if (messages) {
        const modal = new bootstrap.Modal(document.getElementById('agregarProductoModal'));
        modal.show();
    }
});

function toggleListo(productoId) {
    const checkbox = document.getElementById(`switch-${productoId}`);

    // Si el usuario no es superuser, evitar el cambio
    if (checkbox.disabled) {
        return;
    }

    const estadoListo = checkbox.checked;

    fetch(`/producto/toggle_listo/${productoId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ listo: estadoListo }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar la categoría en la tabla
                const categoriaTd = document.getElementById(`categoria-${productoId}`);
                if (categoriaTd) {
                    categoriaTd.innerHTML = `<span class="badge bg-success">${data.categoria}</span>`;
                }
            } else {
                alert('Hubo un error al actualizar el estado.');
                checkbox.checked = !estadoListo;  // Revierte el cambio si hay error
            }
        })
        .catch(error => {
            console.error('Error:', error);
            checkbox.checked = !estadoListo;  // Revierte el cambio si hay error
        });
}

function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue;
}

function aplicarFiltro(campo, valor) {
let url = new URL(window.location.href);
url.searchParams.set(campo, valor);  // Agrega o actualiza el filtro
url.searchParams.set('page', 1);  // Reinicia la paginación para evitar errores
window.location.href = url.toString();  // Redirige con los nuevos filtros
}



function actualizarNotificaciones() {
fetch("{% url 'obtener_notificaciones' %}")
.then(response => response.json())
.then(data => {
    let contador = document.getElementById("contadorNotificaciones");
    let lista = document.getElementById("listaNotificaciones");

    // ✅ Actualizar contador de notificaciones no leídas
    if (data.total_no_leidas > 0) {
        contador.textContent = data.total_no_leidas;
        contador.style.display = "inline-block";
    } else {
        contador.style.display = "none";
    }

    // ✅ Limpiar lista de notificaciones
    lista.innerHTML = "";

    if (data.notificaciones.length > 0) {
        data.notificaciones.forEach(n => {
            let claseLeido = n.leido ? "text-muted" : "fw-bold text-dark";
            lista.innerHTML += `
                <div class="border-bottom py-2 ${claseLeido}" id="notificacion-${n.id}">
                    <small class="d-block text-secondary">${n.fecha}</small>
                    <p class="mb-1 d-inline">${n.mensaje}</p>
                    <button class="btn btn-sm btn-danger float-end" onclick="eliminarNotificacion(${n.id})">🗑️</button>
                </div>`;
        });

        // Agregar botón para eliminar todas
        lista.innerHTML += `
            <div class="text-center mt-3">
                <button id="eliminarTodasBtn" class="btn btn-sm btn-danger w-100" onclick="eliminarTodasNotificaciones()">🗑️ Eliminar todas</button>
            </div>`;
    } else {
        lista.innerHTML = '<p class="text-muted text-center">📭 No tienes nuevas notificaciones</p>';
    }
})
.catch(error => console.error("Error obteniendo notificaciones:", error));
}

// ✅ Eliminar una notificación
function eliminarNotificacion(notificacionId) {
fetch(`/notificaciones/eliminar/${notificacionId}/`, {
method: "DELETE",
headers: { "X-CSRFToken": getCsrfToken() }
})
.then(response => response.json())
.then(data => {
if (data.success) {
    document.getElementById(`notificacion-${notificacionId}`).remove();
    actualizarNotificaciones(); // Actualizar la lista después de eliminar
} else {
    alert("Error al eliminar la notificación.");
}
});
}

// ✅ Eliminar todas las notificaciones
function eliminarTodasNotificaciones() {
if (!confirm("¿Estás seguro de que deseas eliminar todas las notificaciones?")) return;

fetch(`/notificaciones/eliminar_todas/`, {
method: "DELETE",
headers: { "X-CSRFToken": getCsrfToken() }
})
.then(response => response.json())
.then(data => {
if (data.success) {
    document.getElementById("listaNotificaciones").innerHTML = '<p class="text-muted text-center">📭 No tienes nuevas notificaciones</p>';
    actualizarNotificaciones();
} else {
    alert("Error al eliminar todas las notificaciones.");
}
});
}

// ✅ Mostrar/Ocultar el menú desplegable de notificaciones
document.getElementById("notificacionesBtn").addEventListener("click", function(event) {
let dropdown = document.getElementById("notificacionesDropdown");
dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
event.stopPropagation();
});

// ✅ Ocultar el menú si se hace clic fuera
document.addEventListener("click", function(event) {
let dropdown = document.getElementById("notificacionesDropdown");
let btn = document.getElementById("notificacionesBtn");
if (!btn.contains(event.target) && !dropdown.contains(event.target)) {
dropdown.style.display = "none";
}
});

// ✅ Marcar todas como leídas
document.getElementById("marcarLeidasBtn").addEventListener("click", function() {
fetch("{% url 'marcar_notificaciones_leidas' %}", { 
method: "POST", 
headers: { "X-CSRFToken": getCsrfToken() } 
})
.then(response => response.json())
.then(data => {
if (data.success) {
    actualizarNotificaciones();
}
});
});

// ✅ Obtener CSRF Token
function getCsrfToken() {
const cookieValue = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
return cookieValue;
}

// ✅ Actualizar notificaciones cada 5 segundos
setInterval(actualizarNotificaciones, 5000);
actualizarNotificaciones();


function toggleListo(productoId) {
    const checkbox = document.getElementById(`switch-${productoId}`);

    // Si el usuario no es superuser, evitar el cambio
    if (checkbox.disabled) {
        return;
    }

    const estadoListo = checkbox.checked;

    fetch(`/producto/toggle_listo/${productoId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ listo: estadoListo }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // ✅ Actualizar la categoría en la tabla dinámicamente
                const categoriaTd = document.getElementById(`categoria-${productoId}`);
                if (categoriaTd) {
                    let categoriaColor = "bg-secondary"; // Color por defecto (gris)

                    if (data.categoria === "Realizados") {
                        categoriaColor = "bg-success"; // ✅ Verde si es "Realizados"
                    } else if (data.categoria === "Faltantes") {
                        categoriaColor = "bg-danger"; // ✅ Rojo si es "Faltantes"
                    }

                    categoriaTd.innerHTML = `<span class="badge ${categoriaColor}">${data.categoria}</span>`;
                }
            } else {
                alert('Hubo un error al actualizar el estado.');
                checkbox.checked = !estadoListo;  // Revierte el cambio si hay error
            }
        })
        .catch(error => {
            console.error('Error:', error);
            checkbox.checked = !estadoListo;
        });
}

function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue;
}

$(document).ready(function () {
    $("#sku").on("input", function () {
        var sku = $(this).val().trim();

        if (sku.length > 2) { // Para evitar consultas con muy pocos caracteres
            $.ajax({
                url: "{% url 'obtener_descripcion_sku' %}",
                type: "POST",
                data: {
                    "sku": sku,
                    "csrfmiddlewaretoken": "{{ csrf_token }}"
                },
                success: function (response) {
                    if (response.descripcion) {
                        $("#descripcion").val(response.descripcion); // Llena la descripción
                    } else {
                        $("#descripcion").val("No encontrado");
                    }
                },
                error: function () {
                    console.error("Error al obtener la descripción.");
                }
            });
        }
    });
});

$(document).ready(function () {
    $("#editarSku").on("input", function () {
        var sku = $(this).val().trim();

        if (sku.length > 2) { // Evita consultas con pocos caracteres
            $.ajax({
                url: "{% url 'obtener_descripcion_sku' %}",
                type: "POST",
                data: {
                    "sku": sku,
                    "csrfmiddlewaretoken": "{{ csrf_token }}"
                },
                success: function (response) {
                    if (response.descripcion) {
                        $("#editarDescripcion").val(response.descripcion); // Llena la descripción
                    } else {
                        $("#editarDescripcion").val("No encontrado");
                    }
                },
                error: function () {
                    console.error("Error al obtener la descripción.");
                }
            });
        }
    });

    // Rellenar datos del modal de edición cuando se abre
    $('#editarProductoModal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget); // Botón que activó el modal
        var id = button.data('id');
        var sku = button.data('sku');
        var descripcion = button.data('descripcion');
        var precio = button.data('precio');
        var importancia = button.data('importancia');
        var proveedor = button.data('proveedor');
        var nota = button.data('nota');

        $("#editarId").val(id);
        $("#editarSku").val(sku);
        $("#editarDescripcion").val(descripcion);
        $("#editarPrecioCompra").val(precio);
        $("#editarProveedor").val(proveedor);
        $("#editarNota").val(nota);

        if (importancia) {
            $("#editarEstrella" + importancia).prop("checked", true);
        }
    });
});




<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
