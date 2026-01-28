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
  // D. VẼ XE VÀ CHỌN MÀU THEO TRẠNG THÁI
  vehicleData.forEach(function (xe) {
    // 1. Chuẩn hóa trạng thái (để tránh lỗi viết hoa/thường)
    // Nếu status bị null thì gán mặc định là 'available'
    var rawStatus = xe.status ? xe.status.toString() : "available";
    var statusNormal = rawStatus.toLowerCase().trim();

    // 2. Tạo đường dẫn đặt xe (Dựa trên ID xe)
    var bookingUrl = "/bookings/create/" + xe.id + "/";

    // 3. Logic chọn màu Icon (Dựa trên status đã chuẩn hóa)
    var finalIcon;
    if (statusNormal === "booked" || statusNormal === "da_dat") {
      finalIcon = iconRed; // Xe bận -> Đỏ
    } else if (statusNormal === "maintenance" || statusNormal === "bao_tri") {
      finalIcon = iconGrey; // Bảo trì -> Xám
    } else {
      finalIcon = iconGreen; // Còn lại (available) -> Xanh lá
    }

    // 4. Xác định xem xe có rảnh không
    var isAvailable =
      statusNormal === "available" || statusNormal === "san_sang";

    // 5. Logic Style nút bấm (Disabled nếu không rảnh)
    var btnStyle = isAvailable
      ? "cursor:pointer; background: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 3px;"
      : "background: #ccc; cursor: not-allowed; color: #666; border: none; padding: 5px 10px; border-radius: 3px;";

    // 6. Vẽ Marker
    var marker = L.marker([xe.lat, xe.lng], { icon: finalIcon }).addTo(map);

    // 7. Tạo nội dung Popup
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

                <button onclick="${isAvailable ? `window.location.href='${bookingUrl}'` : "return false;"}" 
                    class="popup-btn" 
                    style="${btnStyle}">
                    ${isAvailable ? "Đặt ngay" : "Không khả dụng"}
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
function openModal() {
  document.getElementById("routeModal").style.display = "block";
}

function closeModal() {
  document.getElementById("routeModal").style.display = "none";
}

// Khi click ra ngoài vùng modal thì cũng đóng
window.onclick = function (event) {
  var modal = document.getElementById("routeModal");
  if (event.target == modal) {
    modal.style.display = "none";
  }
};

// --- 6. HÀM VẼ ĐƯỜNG & HIỆN MODAL (NÂNG CẤP) ---
window.chiDuong = function (destLat, destLng) {
  console.log("Đang tính toán đường đi...");

  if (currentRoute) {
    map.removeControl(currentRoute);
  }

  currentRoute = L.Routing.control({
    waypoints: [L.latLng(userLat, userLng), L.latLng(destLat, destLng)],
    routeWhileDragging: false,
    showAlternatives: false,
    show: false, // Vẫn tắt bảng mặc định của Leaflet để dùng Modal xịn của mình
    lineOptions: {
      styles: [{ color: "blue", opacity: 0.6, weight: 6 }],
    },
    createMarker: function () {
      return null;
    },
  })
    .on("routesfound", function (e) {
      // Lấy dữ liệu đường đi đầu tiên
      var route = e.routes[0];
      var summary = route.summary;

      // 1. Tính toán giá tiền & Khoảng cách
      var distanceInKm = (summary.totalDistance / 1000).toFixed(2);
      var pricePerKm = 15000;
      var estimatedPrice = Math.round(distanceInKm * pricePerKm).toLocaleString(
        "vi-VN",
      );
      var timeInMinutes = Math.round(summary.totalTime / 60);

      // 2. Đổ dữ liệu vào phần Tóm tắt (Summary)
      var summaryHTML = `
        <div><b>🏁 Quãng đường:</b> ${distanceInKm} km</div>
        <div><b>⏳ Thời gian dự kiến:</b> ${timeInMinutes} phút</div>
        <div style="font-size: 18px; color: #c0392b; margin-top: 5px;">
            <b>💰 Thành tiền: ${estimatedPrice} VNĐ</b>
        </div>
      `;
      document.getElementById("route-summary").innerHTML = summaryHTML;

      // 3. Xử lý Hướng dẫn đường đi (Instructions)
      // OSRM trả về mảng instructions chứa text, distance, direction...
      var instructions = route.instructions;
      var listHTML = "";

      instructions.forEach(function (step) {
        // Tạo icon mũi tên đơn giản dựa trên text (logic tương đối)
        var icon = "⬆️"; // Mặc định đi thẳng
        if (step.text.includes("Left") || step.text.includes("left"))
          icon = "⬅️";
        if (step.text.includes("Right") || step.text.includes("right"))
          icon = "➡️";
        if (step.text.includes("Arrive") || step.text.includes("destination"))
          icon = "🎯";

        // Dịch sơ bộ sang tiếng Việt
        var textVi = step.text
          .replace("Head", "Đi về hướng")
          .replace("Turn left", "Rẽ trái")
          .replace("Turn right", "Rẽ phải")
          .replace("onto", "vào đường")
          .replace("You have arrived", "Bạn đã đến nơi");

        listHTML += `
            <li>
                <span class="instruction-icon">${icon}</span>
                <div>
                    <div>${textVi}</div>
                    <small style="color: #888;">${step.distance > 0 ? step.distance + " mét" : ""}</small>
                </div>
            </li>
          `;
      });

      document.getElementById("route-instructions").innerHTML = listHTML;

      // 4. Mở Modal lên
      openModal();
    })
    .addTo(map);
};
