// 1. KHAI BÁO BIẾN TOÀN CỤC
var map;
var userMarker; // Biến để quản lý cái ghim đỏ (người dùng)
var currentRoute = null; // Biến để quản lý đường đi đang vẽ

// Tọa độ mặc định (Chợ Bến Thành)
var userLat = 10.7721;
var userLng = 106.6983;

// 2. HÀM KHỞI TẠO BẢN ĐỒ
function initMap(vehicleData) {
  // A. Khởi tạo Map
  map = L.map("map").setView([userLat, userLng], 13);

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap",
  }).addTo(map);

  // B. Tạo Icon (Xe và User)
  var carIcon = L.icon({
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  var userIcon = L.icon({
    // Dùng icon màu đỏ cho nổi bật
    iconUrl:
      "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  // C. Tạo Marker User ở vị trí mặc định trước
  userMarker = L.marker([userLat, userLng], { icon: userIcon })
    .addTo(map)
    .bindPopup("<b>Đang tìm vị trí của bạn...</b>"); // Chưa mở popup vội

  // --- TÍNH NĂNG MỚI: LẤY GPS THỰC TẾ ---
  locateUser();

  // D. Vẽ các xe từ dữ liệu Database
  vehicleData.forEach(function (xe) {
    var marker = L.marker([xe.lat, xe.lng], { icon: carIcon }).addTo(map);

    var popupContent = `
            <div style="text-align: center;">
                <h3 style="margin: 0; color: #007bff;">${xe.plate}</h3>
                <p style="margin: 5px 0;"><b>${xe.name}</b></p>
                <p>Trạng thái: <b>${xe.status}</b></p>

                <button onclick="chiDuong(${xe.lat}, ${xe.lng})" 
                    class="popup-btn" 
                    style="cursor:pointer; background: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 3px; margin-right: 5px;">
                    🚗 Chỉ đường
                </button>

                <button onclick="alert('Đã chọn xe ${xe.plate}')" 
                    class="popup-btn" 
                    style="cursor:pointer; background: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 3px;">
                    Đặt ngay
                </button>
            </div>
        `;
    marker.bindPopup(popupContent);
  });
}

// 3. HÀM XỬ LÝ GEOLOCATION (Lấy vị trí thực)
function locateUser() {
  // Kiểm tra xem trình duyệt có hỗ trợ không
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      // Nếu thành công (User bấm Allow)
      function (position) {
        // 1. Cập nhật tọa độ mới vào biến toàn cục
        userLat = position.coords.latitude;
        userLng = position.coords.longitude;
        console.log("Đã tìm thấy vị trí:", userLat, userLng);

        // 2. Di chuyển marker đỏ đến vị trí mới
        userMarker.setLatLng([userLat, userLng]);
        userMarker.bindPopup("<b>Bạn đang ở đây!</b>").openPopup();

        // 3. Hiệu ứng bay đến vị trí đó (nhìn cho mượt)
        map.flyTo([userLat, userLng], 14, {
          duration: 1.5, // Bay trong 1.5 giây
        });
      },
      // Nếu thất bại (User chặn hoặc lỗi)
      function (error) {
        console.warn("Không lấy được vị trí, dùng mặc định:", error.message);
        userMarker
          .bindPopup("<b>Không lấy được GPS</b><br>Đang dùng vị trí mặc định.")
          .openPopup();
      },
    );
  } else {
    console.error("Trình duyệt không hỗ trợ Geolocation");
  }
}

// 4. HÀM VẼ ĐƯỜNG (Gọi từ nút bấm trong Popup xe)
window.chiDuong = function (destLat, destLng) {
  console.log("Vẽ đường từ", userLat, userLng, "đến", destLat, destLng);

  // Xóa đường cũ nếu có
  if (currentRoute) {
    map.removeControl(currentRoute);
  }

  // Gọi Routing Machine
  currentRoute = L.Routing.control({
    waypoints: [
      L.latLng(userLat, userLng), // Luôn dùng tọa độ mới nhất của User
      L.latLng(destLat, destLng),
    ],
    routeWhileDragging: false,
    showAlternatives: false,
    show: false, // Tắt bảng chỉ dẫn text
    lineOptions: {
      styles: [{ color: "blue", opacity: 0.6, weight: 6 }],
    },
    createMarker: function () {
      return null;
    }, // Không tạo thêm marker thừa
  }).addTo(map);
};
