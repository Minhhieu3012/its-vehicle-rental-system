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

  // --- B. ĐỊNH NGHĨA ICON CHUYÊN NGHIỆP (SVG) ---

  // Hàm tạo icon hình chiếc xe bằng mã SVG (Không cần tải ảnh)
  function createCarIcon(color) {
    var svgHtml = `
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="35" height="35">
              <path fill="${color}" stroke="white" stroke-width="20" d="M112 112c0-26.5 21.5-48 48-48h192c26.5 0 48 21.5 48 48v288c0 26.5-21.5 48-48 48H160c-26.5 0-48-21.5-48-48V112z"/>
              <path fill="rgba(255,255,255,0.5)" d="M160 128h192v64H160z"/> <circle cx="120" cy="144" r="20" fill="#333"/> <circle cx="392" cy="144" r="20" fill="#333"/>
              <circle cx="120" cy="368" r="20" fill="#333"/>
              <circle cx="392" cy="368" r="20" fill="#333"/>
          </svg>
      `;

    return L.divIcon({
      className: "custom-car-icon",
      html: svgHtml,
      iconSize: [35, 35], // Kích thước icon
      iconAnchor: [17, 17], // Căn giữa tâm (để marker nằm đúng vị trí)
      popupAnchor: [0, -10], // Popup hiện lên trên một chút
    });
  }

  // Tạo 3 loại icon xe theo màu sắc
  var iconGreen = createCarIcon("#28a745"); // Xanh lá (Available)
  var iconRed = createCarIcon("#dc3545"); // Đỏ (Booked)
  var iconGrey = createCarIcon("#6c757d"); // Xám (Maintenance)

  // Icon User (Vẫn giữ kiểu Pin màu Vàng để phân biệt với xe)
  var userIcon = L.icon({
    iconUrl:
      "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-gold.png",
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
    // 1. Chuẩn hóa trạng thái
    var rawStatus = xe.status ? xe.status.toString() : "available";
    var statusNormal = rawStatus.toLowerCase().trim();

    // 2. Tạo link đặt xe
    var bookingUrl = "/bookings/create/" + xe.id + "/";

    // 3. Logic chọn icon SVG
    var finalIcon;
    if (statusNormal === "booked" || statusNormal === "da_dat") {
      finalIcon = iconRed;
    } else if (statusNormal === "maintenance" || statusNormal === "bao_tri") {
      finalIcon = iconGrey;
    } else {
      finalIcon = iconGreen;
    }

    // 4. Logic nút bấm
    var isAvailable =
      statusNormal === "available" || statusNormal === "san_sang";
    var btnStyle = isAvailable
      ? "cursor:pointer; background: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 3px;"
      : "background: #ccc; cursor: not-allowed; color: #666; border: none; padding: 5px 10px; border-radius: 3px;";

    // 5. Vẽ Marker
    var marker = L.marker([xe.lat, xe.lng], { icon: finalIcon }).addTo(map);

    // 6. Nội dung Popup
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

// 3. CÁC HÀM XỬ LÝ MODAL (UI/UX)
function openModal() {
  document.getElementById("routeModal").style.display = "block";
}

function closeModal() {
  document.getElementById("routeModal").style.display = "none";
}

window.onclick = function (event) {
  var modal = document.getElementById("routeModal");
  if (event.target == modal) {
    modal.style.display = "none";
  }
};

// 4. HÀM XỬ LÝ GEOLOCATION
function locateUser() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function (position) {
        userLat = position.coords.latitude;
        userLng = position.coords.longitude;
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

// 5. HÀM VẼ ĐƯỜNG & HIỆN MODAL
window.chiDuong = function (destLat, destLng) {
  console.log("Đang tính toán đường đi...");

  if (currentRoute) {
    map.removeControl(currentRoute);
  }

  currentRoute = L.Routing.control({
    waypoints: [L.latLng(userLat, userLng), L.latLng(destLat, destLng)],
    routeWhileDragging: false,
    showAlternatives: false,
    show: false, // Tắt bảng mặc định để dùng Modal
    lineOptions: {
      styles: [{ color: "blue", opacity: 0.6, weight: 6 }],
    },
    createMarker: function () {
      return null;
    },
  })
    .on("routesfound", function (e) {
      // Lấy dữ liệu đường đi
      var route = e.routes[0];
      var summary = route.summary;

      // Tính toán
      var distanceInKm = (summary.totalDistance / 1000).toFixed(2);
      var pricePerKm = 15000;
      var estimatedPrice = Math.round(distanceInKm * pricePerKm).toLocaleString(
        "vi-VN",
      );
      var timeInMinutes = Math.round(summary.totalTime / 60);

      // Đổ vào Modal - Phần Tóm tắt
      var summaryHTML = `
        <div><b>🏁 Quãng đường:</b> ${distanceInKm} km</div>
        <div><b>⏳ Thời gian dự kiến:</b> ${timeInMinutes} phút</div>
        <div style="font-size: 18px; color: #c0392b; margin-top: 5px;">
            <b>💰 Thành tiền: ${estimatedPrice} VNĐ</b>
        </div>
      `;
      document.getElementById("route-summary").innerHTML = summaryHTML;

      // Đổ vào Modal - Phần Hướng dẫn
      var instructions = route.instructions;
      var listHTML = "";

      instructions.forEach(function (step) {
        var icon = "⬆️";
        if (step.text.includes("Left") || step.text.includes("left"))
          icon = "⬅️";
        if (step.text.includes("Right") || step.text.includes("right"))
          icon = "➡️";
        if (step.text.includes("Arrive") || step.text.includes("destination"))
          icon = "🎯";

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
      openModal();
    })
    .addTo(map);
};
