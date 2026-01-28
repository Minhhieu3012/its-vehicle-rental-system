var map;
var currentRoute = null;
var userLat = 10.7721; // Mặc định: Chợ Bến Thành
var userLng = 106.6983;

function initMap(vehicleData) {
  // 1. Khởi tạo bản đồ
  map = L.map("map").setView([10.762622, 106.660172], 13);

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap",
  }).addTo(map);

  // 2. Cấu hình Icon
  var carIcon = L.icon({
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  var userIcon = L.icon({
    iconUrl:
      "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  // 3. Hiển thị User Marker
  L.marker([userLat, userLng], { icon: userIcon })
    .addTo(map)
    .bindPopup("<b>Vị trí của bạn</b>")
    .openPopup();

  // 4. Vẽ Marker Xe từ dữ liệu được truyền vào
  vehicleData.forEach(function (xe) {
    var marker = L.marker([xe.lat, xe.lng], { icon: carIcon }).addTo(map);

    var popupContent = `
            <div style="text-align: center;">
                <h3 style="margin: 0; color: #007bff;">${xe.plate}</h3>
                <p style="margin: 5px 0;"><b>${xe.name}</b></p>
                <p>Trạng thái: <b>${xe.status}</b></p>

                <button onclick="chiDuong(${xe.lat}, ${xe.lng})" 
                    class="popup-btn" style="background: #28a745; margin-right: 5px;">
                    🚗 Chỉ đường
                </button>

                <button onclick="alert('Đã gửi yêu cầu đặt xe!')" 
                    class="popup-btn" style="background: #007bff;">
                    Đặt ngay
                </button>
            </div>
        `;
    marker.bindPopup(popupContent);
  });
}

// --- HÀM VẼ ĐƯỜNG (ITS Feature) ---
window.chiDuong = function (destLat, destLng) {
  if (currentRoute) {
    map.removeControl(currentRoute);
  }

  currentRoute = L.Routing.control({
    waypoints: [L.latLng(userLat, userLng), L.latLng(destLat, destLng)],
    routeWhileDragging: false,
    showAlternatives: true,
    serviceUrl: "https://router.project-osrm.org/route/v1",
    lineOptions: {
      styles: [{ color: "blue", opacity: 0.7, weight: 6 }],
    },
    createMarker: function () {
      return null;
    },
    show: true, // Bảng chỉ dẫn text
  }).addTo(map);
};
