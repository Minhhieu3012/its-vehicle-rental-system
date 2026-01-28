// 1. KHAI BÁO BIẾN TOÀN CỤC
var map;
var userMarker;
var currentRoute = null;

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

  // --- B. ĐỊNH NGHĨA BỘ ICON (MÀU SẮC KHÁC NHAU) ---
  // Icon cho xe Sẵn sàng (Available) - Màu Xanh Lá
  var iconGreen = L.icon({
    iconUrl:
      "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  // Icon cho xe Đã đặt (Booked) - Màu Đỏ (Theo yêu cầu)
  var iconRed = L.icon({
    iconUrl:
      "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-gold.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  // Icon cho xe Bảo trì (Maintenance) - Màu Xám
  var iconGrey = L.icon({
    iconUrl:
      "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  // Icon User - Màu Vàng (Gold) để không bị trùng với xe màu Đỏ
  var userIcon = L.icon({
    iconUrl:
      "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  // C. Tạo Marker User
  userMarker = L.marker([userLat, userLng], { icon: userIcon })
    .addTo(map)
    .bindPopup("<b>Bạn đang ở đây</b>");

  // Gọi hàm lấy GPS
  locateUser();

  // D. VẼ XE VÀ CHỌN MÀU THEO TRẠNG THÁI
  vehicleData.forEach(function (xe) {
    // --- LOGIC CHỌN MÀU ---
    var finalIcon;
    var statusText = xe.status; // Lấy trạng thái

    if (statusText === "booked") {
      finalIcon = iconRed; // Xe bận -> Đỏ
    } else if (statusText === "maintenance") {
      finalIcon = iconGrey; // Bảo trì -> Xám
    } else {
      finalIcon = iconGreen; // Còn lại (available) -> Xanh lá
    }

    var marker = L.marker([xe.lat, xe.lng], { icon: finalIcon }).addTo(map);

    // Chỉ hiện nút "Đặt xe" nếu xe đang Available
    // Nếu xe bận hoặc bảo trì thì ẩn nút đi (disabled)
    var btnStyle =
      "cursor:pointer; background: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 3px;";
    if (statusText !== "available") {
      btnStyle =
        "background: #ccc; cursor: not-allowed; color: #666; border: none; padding: 5px 10px; border-radius: 3px;";
    }

    var popupContent = `
            <div style="text-align: center;">
                <h3 style="margin: 0; color: #007bff;">${xe.plate}</h3>
                <p style="margin: 5px 0;"><b>${xe.name}</b></p>
                <p>Trạng thái: <b>${xe.status}</b></p>

                <button onclick="chiDuong(${xe.lat}, ${xe.lng})" 
                    class="popup-btn" 
                    style="cursor:pointer; background: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 3px; margin-right: 5px;">
                    🚗 Chỉ đường & Tính giá
                </button>

                <button onclick="${statusText === "available" ? `alert('Đã chọn xe ${xe.plate}')` : "return false;"}" 
                    class="popup-btn" 
                    style="${btnStyle}">
                    ${statusText === "available" ? "Đặt ngay" : "Không khả dụng"}
                </button>
            </div>
        `;
    marker.bindPopup(popupContent);
  });
}

// 3. HÀM XỬ LÝ GEOLOCATION
function locateUser() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function (position) {
        userLat = position.coords.latitude;
        userLng = position.coords.longitude;
        console.log("Đã tìm thấy vị trí:", userLat, userLng);

        userMarker.setLatLng([userLat, userLng]);
        userMarker.bindPopup("<b>Bạn đang ở đây!</b>").openPopup();
        map.flyTo([userLat, userLng], 14, { duration: 1.5 });
      },
      function (error) {
        console.warn("Lỗi GPS:", error.message);
      },
    );
  }
}

// 4. HÀM VẼ ĐƯỜNG & TÍNH TIỀN
window.chiDuong = function (destLat, destLng) {
  console.log("Đang tính toán đường đi...");

  if (currentRoute) {
    map.removeControl(currentRoute);
  }

  currentRoute = L.Routing.control({
    waypoints: [L.latLng(userLat, userLng), L.latLng(destLat, destLng)],
    routeWhileDragging: false,
    showAlternatives: false,
    show: false, // Tắt bảng chỉ dẫn
    lineOptions: {
      styles: [{ color: "blue", opacity: 0.6, weight: 6 }],
    },
    createMarker: function () {
      return null;
    },
  })
    .on("routesfound", function (e) {
      // --- LOGIC LẤY KHOẢNG CÁCH ---
      var routes = e.routes;
      var summary = routes[0].summary;

      // summary.totalDistance: đơn vị là mét (m)
      var distanceInKm = (summary.totalDistance / 1000).toFixed(2); // Đổi ra km, lấy 2 số lẻ

      // Ví dụ: Giá cước 15.000 VNĐ / km
      var pricePerKm = 15000;
      var estimatedPrice = Math.round(distanceInKm * pricePerKm);

      // Format tiền tệ cho đẹp (ví dụ: 200.000)
      var formattedPrice = estimatedPrice.toLocaleString("vi-VN");

      // Hiển thị thông báo (Sau này bạn có thể gán vào thẻ HTML thay vì alert)
      alert(
        `🚗 Quãng đường: ${distanceInKm} km\n💰 Ước tính chi phí di chuyển đến xe: ${formattedPrice} VNĐ`,
      );

      console.log("Khoảng cách (m):", summary.totalDistance);
      console.log("Thời gian (giây):", summary.totalTime);
    })
    .addTo(map);
};
