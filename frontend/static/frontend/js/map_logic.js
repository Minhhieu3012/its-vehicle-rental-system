// ======================
// 1. BIẾN TOÀN CỤC (GLOBAL)
// ======================
var map;
var userMarker;
var searchMarker;
var allMarkers = []; // Lưu trữ tất cả marker để lọc
var currentRoute = null;
var userLat = null;
var userLng = null;

const DEFAULT_LAT = 10.762622;
const DEFAULT_LNG = 106.660172;

// ======================
// 2. LOGIC BẢN ĐỒ & MARKER
// ======================

function initMap(vehicleData) {
    // Khởi tạo bản đồ
    map = L.map("map", { zoomControl: false }).setView([DEFAULT_LAT, DEFAULT_LNG], 12);
    L.control.zoom({ position: 'bottomright' }).addTo(map); // Chuyển nút zoom xuống góc dưới

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap",
    }).addTo(map);

    // Hàm tạo Icon SVG động theo màu
    function createCarIcon(color) {
        var svgHtml = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="35" height="35">
            <path fill="${color}" stroke="white" stroke-width="20" d="M112 112c0-26.5 21.5-48 48-48h192c26.5 0 48 21.5 48 48v288c0 26.5-21.5 48-48 48H160c-26.5 0-48-21.5-48-48V112z"/>
            <path fill="rgba(255,255,255,0.5)" d="M160 128h192v64H160z"/><circle cx="120" cy="144" r="20" fill="#333"/><circle cx="392" cy="144" r="20" fill="#333"/><circle cx="120" cy="368" r="20" fill="#333"/><circle cx="392" cy="368" r="20" fill="#333"/></svg>`;
        return L.divIcon({
            className: "custom-car-icon",
            html: svgHtml,
            iconSize: [35, 35],
            iconAnchor: [17, 17],
            popupAnchor: [0, -10],
        });
    }

    const icons = {
        green: createCarIcon("#28a745"),   // Available
        blue: createCarIcon("#007bff"),    // In Use
        red: createCarIcon("#dc3545"),     // Maintenance
        yellow: createCarIcon("#ffc107"),  // Booked
    };

    // Lấy vị trí người dùng ngay khi map load
    getUserLocation();

    // Duyệt qua danh sách xe và vẽ Marker
    vehicleData.forEach(function (xe) {
        // Chuẩn hóa tọa độ (xử lý trường hợp tên biến khác nhau)
        xe.lat = xe.latitude || xe.lat;
        xe.lng = xe.longitude || xe.lng;

        if (!xe.lat || !xe.lng) return;

        // Xử lý trạng thái & Config hiển thị
        var rawStatus = xe.status ? xe.status.toString() : "available";
        var statusNormal = rawStatus.toLowerCase().trim().replace(/_/g, " ");
        var bookingUrl = "/thue-xe/" + xe.id + "/";

        var statusConfig = {
            label: "Sẵn sàng",
            color: "#28a745",
            icon: icons.green,
            btnText: "THUÊ NGAY",
            btnColor: "#28a745",
            isBookable: true,
            bookingAction: "book_now",
            note: "✅ Xe đang rảnh, có thể nhận ngay!",
        };

        if (statusNormal.includes("maintenance") || statusNormal.includes("bao tri")) {
            statusConfig = {
                label: "Bảo trì",
                color: "#dc3545",
                icon: icons.red,
                btnText: "ĐANG BẢO TRÌ",
                btnColor: "#dc3545",
                isBookable: false,
                note: "⚠️ Xe đang bảo dưỡng. Vui lòng chọn xe khác.",
            };
        } else if (statusNormal.includes("in operation") || statusNormal.includes("in use")) {
            statusConfig = {
                label: "Đang hoạt động",
                color: "#007bff",
                icon: icons.blue,
                btnText: "ĐẶT LỊCH",
                btnColor: "#007bff",
                isBookable: true,
                bookingAction: "book_later",
                note: "🔵 Khách đang thuê. Bạn có thể đặt lịch trước.",
            };
        } else if (statusNormal.includes("booked") || statusNormal.includes("da dat")) {
            statusConfig = {
                label: "Đã có khách",
                color: "#ffc107",
                icon: icons.yellow,
                btnText: "CHỌN NGÀY KHÁC",
                btnColor: "#e0a800",
                isBookable: true,
                bookingAction: "book_alternative",
                note: "🟡 Xe đã được đặt trước.",
            };
        }

        // Tạo Marker và Bind Popup
        var marker = L.marker([xe.lat, xe.lng], { icon: statusConfig.icon }).addTo(map);
        
        // Lưu thuộc tính vào marker để dùng cho bộ lọc
        marker.id = xe.id;
        marker.status = statusNormal; // Lưu trạng thái chuẩn hóa

        allMarkers.push(marker);

        // Nội dung Popup HTML
        var safeName = xe.name.replace(/'/g, "\\'").replace(/"/g, "&quot;");
        var smartBookingUrl = statusConfig.bookingAction ? `${bookingUrl}?action=${statusConfig.bookingAction}` : bookingUrl;

        var popupContent = `
            <div style="font-family: 'Segoe UI', sans-serif; min-width: 250px;">
                <h3 style="margin: 0 0 5px 0; font-size: 16px; color: #2c3e50; font-weight: 700;">${xe.name}</h3>
                <div style="margin-bottom: 8px; display: flex; justify-content: space-between;">
                    <span style="border: 1px solid ${statusConfig.color}; color: ${statusConfig.color}; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 700;">${statusConfig.label}</span>
                    <small>⭐ ${xe.rating || 5.0} (${xe.trips || 0})</small>
                </div>
                <div style="background: #f8f9fa; padding: 10px; border-radius: 6px; border-left: 4px solid ${statusConfig.color}; margin-bottom: 10px;">
                    <div style="color: #d63031; font-size: 18px; font-weight: bold;">${parseInt(xe.price).toLocaleString("vi-VN")}đ</div>
                    <small style="color: #666;">/ngày</small>
                </div>
                <div style="display: flex; gap: 5px;">
                    <button onclick="openLocationModal('${safeName}', ${xe.lat}, ${xe.lng})" class="popup-btn" style="flex:1; background:#fff; color:#17a2b8; border:1px solid #17a2b8;">📍 Vị trí</button>
                    <button onclick="openTermsModal('${safeName}', ${xe.price})" class="popup-btn" style="flex:1; background:#6c757d;">📄 HĐ</button>
                    <button onclick="${statusConfig.isBookable ? `window.location.href='${smartBookingUrl}'` : "return false;"}" 
                            class="popup-btn" style="flex:2; background:${statusConfig.btnColor}; cursor:${statusConfig.isBookable ? 'pointer' : 'not-allowed'}">
                        ${statusConfig.btnText}
                    </button>
                </div>
            </div>
        `;
        marker.bindPopup(popupContent);
    });
}

// ======================
// 3. CÁC HÀM TIỆN ÍCH (Global)
// ======================

// Hàm bay đến xe (Gọi từ Sidebar HTML)
window.focusVehicle = function(lat, lng) {
    if (map && lat && lng) {
        map.flyTo([lat, lng], 17, { duration: 1.5 });
        // Tìm marker tại vị trí đó để mở popup (Optional)
        allMarkers.forEach(m => {
            var mLat = m.getLatLng().lat;
            var mLng = m.getLatLng().lng;
            // So sánh gần đúng vì float
            if (Math.abs(mLat - lat) < 0.0001 && Math.abs(mLng - lng) < 0.0001) {
                m.openPopup();
            }
        });
    }
};

function getUserLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            userLat = position.coords.latitude;
            userLng = position.coords.longitude;
            
            var userIcon = L.icon({
                iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-violet.png",
                shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
            });

            if (userMarker) userMarker.setLatLng([userLat, userLng]);
            else userMarker = L.marker([userLat, userLng], { icon: userIcon }).addTo(map).bindPopup("Bạn ở đây!");
        });
    }
}

// ======================
// 4. ROUTING & OSRM LOGIC
// ======================
window.calculateRoute = function (destLat, destLng) {
    if (!userLat || !userLng) {
        alert("Đang lấy vị trí của bạn... Vui lòng thử lại sau!");
        getUserLocation();
        return;
    }

    // Reset UI
    document.getElementById("route-summary").innerHTML = '<div style="text-align:center; padding: 20px;">⏳ Đang tính toán lộ trình...</div>';
    document.getElementById("route-instructions").innerHTML = '';
    window.openModal("routeModal");

    if (currentRoute) map.removeControl(currentRoute);

    currentRoute = L.Routing.control({
        waypoints: [L.latLng(userLat, userLng), L.latLng(destLat, destLng)],
        routeWhileDragging: false,
        show: false, // Ẩn bảng chỉ dẫn mặc định của OSRM
        lineOptions: { styles: [{ color: "#007bff", opacity: 0.8, weight: 6 }] },
        createMarker: () => null // Không tạo marker điểm đầu cuối
    }).on("routesfound", function (e) {
        var route = e.routes[0];
        var distKm = (route.summary.totalDistance / 1000).toFixed(1);
        var timeMin = Math.round(route.summary.totalTime / 60);
        var cost = (distKm * 30000).toLocaleString("vi-VN");

        // Render Summary
        var summaryHTML = `
            <div style="display:flex; justify-content:space-around; text-align:center; margin-bottom:15px;">
                <div><div style="font-size:12px; color:#666;">Quãng đường</div><strong>${distKm} km</strong></div>
                <div><div style="font-size:12px; color:#666;">Thời gian</div><strong>${timeMin} phút</strong></div>
                <div><div style="font-size:12px; color:#666;">Phí Ship</div><strong style="color:#d63031;">${cost}đ</strong></div>
            </div>`;
        document.getElementById("route-summary").innerHTML = summaryHTML;

        // Render & Translate Instructions
        var listHTML = "";
        route.instructions.forEach(step => {
            var text = step.text;
            // --- LOGIC DỊCH THUẬT (Regex) ---
            var viText = text
                .replace(/Head/g, "Đi về hướng").replace(/North/g, "Bắc").replace(/South/g, "Nam")
                .replace(/East/g, "Đông").replace(/West/g, "Tây")
                .replace(/Turn right/g, "Rẽ phải").replace(/Turn left/g, "Rẽ trái")
                .replace(/Make a U-turn/g, "Quay đầu").replace(/Roundabout/g, "Vòng xoay")
                .replace(/Arrive at/g, "Đến").replace(/destination/g, "điểm đến")
                .replace(/on the right/g, "bên phải").replace(/on the left/g, "bên trái");
            
            var icon = viText.includes("phải") ? "➡️" : viText.includes("trái") ? "⬅️" : viText.includes("thẳng") ? "⬆️" : "📍";
            
            listHTML += `<li style="padding:8px 0; border-bottom:1px solid #eee; display:flex; gap:10px;">
                <span>${icon}</span>
                <div>${viText} <small style="color:#888;">(${Math.round(step.distance)}m)</small></div>
            </li>`;
        });
        document.getElementById("route-instructions").innerHTML = listHTML;
    }).addTo(map);
};

// ======================
// 5. QUẢN LÝ MODAL (Window Scope)
// ======================
window.openModal = function(id) {
    var m = document.getElementById(id || "routeModal");
    if (m) m.style.display = "flex";
};
window.closeModal = function() { 
    document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = "none");
};
window.openTermsModal = function(name, price) {
    document.getElementById("term-car-name").innerText = name;
    document.getElementById("term-car-price").innerText = parseInt(price).toLocaleString("vi-VN") + "đ/ngày";
    document.getElementById("termsModal").style.display = "flex";
};
window.openLocationModal = function(name, lat, lng) {
    document.getElementById("loc-car-name").innerText = name;
    document.getElementById("locationModal").style.display = "flex";
    
    // Gán sự kiện cho nút trong modal
    document.getElementById("btn-view-map").onclick = function() {
        window.closeModal();
        window.focusVehicle(lat, lng);
    };
    document.getElementById("btn-start-route").onclick = function() {
        window.closeModal();
        window.calculateRoute(lat, lng);
    };
};

// Đóng modal khi click ra ngoài
window.onclick = function(e) {
    if (e.target.classList.contains("modal-overlay")) window.closeModal();
};

// ======================
// 6. KHỞI TẠO CHÍNH (MAIN)
// ======================
document.addEventListener("DOMContentLoaded", function () {
    // 1. Load Data
    var scriptTag = document.getElementById("vehicles-data");
    if (!scriptTag) return console.warn("Không có dữ liệu xe!");
    
    var vehicles = JSON.parse(scriptTag.textContent);
    initMap(vehicles);

    // 2. Chặn sự kiện click xuyên qua Sidebar
    var sidebar = document.querySelector('.sidebar-container');
    if (sidebar) L.DomEvent.disableClickPropagation(sidebar);

    // 3. Xử lý Logic Tìm kiếm Địa chỉ
    var searchInput = document.getElementById("location-search");
    if (searchInput) {
        L.DomEvent.disableClickPropagation(searchInput);
        searchInput.addEventListener("keydown", function(e) {
            if (e.key === "Enter") {
                e.preventDefault();
                var query = this.value;
                fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data && data.length > 0) {
                            var lat = data[0].lat, lon = data[0].lon;
                            if (searchMarker) map.removeLayer(searchMarker);
                            searchMarker = L.marker([lat, lon]).addTo(map).bindPopup(query).openPopup();
                            map.flyTo([lat, lon], 15);
                        } else {
                            alert("Không tìm thấy địa chỉ!");
                        }
                    });
            }
        });
    }

    // 4. Hợp nhất Logic Lọc (Filter) - Xử lý cả Map và Sidebar cùng lúc
    function applyUnifiedFilter(filterValue) {
        var filterNormal = filterValue.toLowerCase();
        
        // A. Lọc trên Bản đồ
        allMarkers.forEach(marker => {
            var status = (marker.status || "").toLowerCase();
            var isVisible = (filterNormal === 'all') || 
                            (filterNormal === 'available' && status === 'available') ||
                            (filterNormal === 'booked' && (status.includes('booked') || status.includes('in use')));
            
            if (isVisible) map.addLayer(marker);
            else map.removeLayer(marker);
        });

        // B. Lọc trên Sidebar (DOM)
        var count = 0;
        document.querySelectorAll(".vehicle-card").forEach((card, index) => {
            // Lấy status từ dữ liệu gốc (vehicles array) dựa trên index
            // Lưu ý: Cách này đúng nếu thứ tự render sidebar khớp với thứ tự array
            var v = vehicles[index]; 
            var status = (v.status || "").toLowerCase();
            var isVisible = (filterNormal === 'all') || 
                            (filterNormal === 'available' && status === 'available') ||
                            (filterNormal === 'booked' && (status.includes('booked') || status.includes('in use')));
            
            card.style.display = isVisible ? "block" : "none";
            if (isVisible) count++;
        });

        // Cập nhật số lượng
        var countEl = document.getElementById("vehicle-count");
        if (countEl) countEl.innerText = `${count} xe tìm thấy`;
    }

    // Gán sự kiện click cho các nút lọc
    document.querySelectorAll(".filter-btn").forEach(btn => {
        btn.addEventListener("click", function() {
            // UI Active state
            document.querySelectorAll(".filter-btn").forEach(b => {
                b.classList.remove("bg-primary", "text-white");
                b.classList.add("bg-slate-100", "text-slate-600"); // Reset style cũ
            });
            this.classList.remove("bg-slate-100", "text-slate-600");
            this.classList.add("bg-primary", "text-white");

            // Gọi hàm lọc
            applyUnifiedFilter(this.dataset.filter);
        });
    });

    // 5. Nút định vị tôi
    var gpsBtn = document.getElementById("locate-me-btn");
    if (gpsBtn) gpsBtn.addEventListener("click", getUserLocation);
});