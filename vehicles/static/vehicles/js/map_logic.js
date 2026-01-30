// KHAI BÁO BIẾN TOÀN CỤC
var map;
var userMarker;
var currentRoute = null;

// Tọa độ mặc định (Chợ Bến Thành)
var userLat = 10.7721;
var userLng = 106.6983;

// HÀM KHỞI TẠO BẢN ĐỒ
function initMap(vehicleData) {
  // Khởi tạo Map
  map = L.map("map").setView([userLat, userLng], 13);

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap",
  }).addTo(map);

  // Định nghĩa icon (SVG)
  function createCarIcon(color) {
    var svgHtml = `
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="35" height="35">
              <path fill="${color}" stroke="white" stroke-width="20" d="M112 112c0-26.5 21.5-48 48-48h192c26.5 0 48 21.5 48 48v288c0 26.5-21.5 48-48 48H160c-26.5 0-48-21.5-48-48V112z"/>
              <path fill="rgba(255,255,255,0.5)" d="M160 128h192v64H160z"/>
              <circle cx="120" cy="144" r="20" fill="#333"/>
              <circle cx="392" cy="144" r="20" fill="#333"/>
              <circle cx="120" cy="368" r="20" fill="#333"/>
              <circle cx="392" cy="368" r="20" fill="#333"/>
          </svg>
      `;
    return L.divIcon({
      className: "custom-car-icon",
      html: svgHtml,
      iconSize: [35, 35],
      iconAnchor: [17, 17],
      popupAnchor: [0, -10],
    });
  }

  // Cập nhật màu
  var iconGreen = createCarIcon("#28a745"); // Available
  var iconYellow = createCarIcon("#ffc107"); // Booked
  var iconBlue = createCarIcon("#007bff"); // In Operation
  var iconRed = createCarIcon("#dc3545"); // Maintenance

  // Icon User
  var userIcon = L.icon({
    iconUrl:
      "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-violet.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  // Tạo Marker User
  userMarker = L.marker([userLat, userLng], { icon: userIcon })
    .addTo(map)
    .bindPopup("<b>Bạn đang ở đây</b>");

  locateUser();

  // Vẽ xe và chọn màu theo trạng thái
  vehicleData.forEach(function (xe) {
    // 1. Chuẩn hóa trạng thái
    var rawStatus = xe.status ? xe.status.toString() : "available";
    var statusNormal = rawStatus.toLowerCase().trim().replace(/_/g, " ");

    // 2. Tạo link đặt xe
    var bookingUrl = "/bookings/create/" + xe.id + "/";

    // 3. Logic chọn icon (4 Cấp độ)
    var statusDisplay = xe.status;
    var finalIcon;

    if (statusNormal === "maintenance" || statusNormal === "bao tri") {
      finalIcon = iconRed; // Bảo trì
      statusDisplay = "Bảo trì 🔴";
    } else if (
      statusNormal === "in operation" ||
      statusNormal === "dang hoat dong"
    ) {
      finalIcon = iconBlue; // Đang chạy
      statusDisplay = "Đang hoạt động 🔵";
    } else if (statusNormal === "booked" || statusNormal === "da dat") {
      finalIcon = iconYellow; // Đã đặt (nhưng chưa lấy xe)
      statusDisplay = "Đã đặt 🟡";
    } else {
      finalIcon = iconGreen; // Sẵn sàng (Mặc định)
      statusDisplay = "Sẵn sàng 🟢";
    }

    // Logic nút bấm
    // Các trạng thái khác (Booked, In Operation, Maintenance) không thể đặt
    var isAvailable =
      statusNormal === "available" || statusNormal === "san sang";

    var btnStyle = isAvailable
      ? "cursor:pointer; background: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 3px;"
      : "background: #ccc; cursor: not-allowed; color: #666; border: none; padding: 5px 10px; border-radius: 3px;";

    // Vẽ Marker
    var marker = L.marker([xe.lat, xe.lng], { icon: finalIcon }).addTo(map);

    // Nội dung Popup
    var popupContent = `
            <div style="text-align: center;">
                <h3 style="margin: 0; color: #007bff;">${xe.plate}</h3>
                <p style="margin: 5px 0;"><b>${xe.name}</b></p>

                <p>Trạng thái: <b>${statusDisplay}</b></p>

                <button onclick="chiDuong(${xe.lat}, ${xe.lng})" 
                    class="popup-btn" 
                    style="cursor:pointer; background: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 3px; margin-right: 5px;">
                    🚗 Chỉ đường
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

// Hàm xử lý Modal
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

// Hàm xử lý Geolocation
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

// Hàm vẽ đường và hiện Modal chỉ đường
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
        var text = step.text;

        // Dịch sang tiếng Việt (Regex)
        var textVi = step.text
          .replace(/Head/g, "Đi về hướng")
          .replace(/Continue/g, "Tiếp tục đi")
          .replace(/Turn left/g, "Rẽ trái")
          .replace(/Turn right/g, "Rẽ phải")
          .replace(/Make a U-turn/g, "Quay đầu xe")
          .replace(/Make a slight left/g, "Chếch sang trái")
          .replace(/Make a slight right/g, "Chếch sang phải")
          .replace(/Keep left/g, "Đi sang làn trái")
          .replace(/Keep right/g, "Đi sang làn phải")
          .replace(/onto/g, "vào đường")
          .replace(/on /g, "trên đường ")
          .replace(/to /g, "đến ")
          .replace(/Enter the roundabout/g, "Vào vòng xoay")
          .replace(/and take the/g, "và đi theo")
          .replace(/exit/g, "lối ra")
          .replace(/(\d+)th/g, "thứ $1")
          .replace("You have arrived at your destination", "Bạn đã đến đích")
          .replace("You have arrived", "Bạn đã đến nơi")
          .replace("at your destination", "")
          .trim();

        // Logic chọn icon theo hướng
        if (text.includes("Left") || text.includes("left")) icon = "⬅️";
        if (text.includes("Right") || text.includes("right")) icon = "➡️";
        if (text.includes("U-turn")) icon = "↩️";
        if (text.includes("roundabout")) icon = "🔄";
        if (text.includes("Arrive") || text.includes("destination"))
          icon = "🎯";

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
