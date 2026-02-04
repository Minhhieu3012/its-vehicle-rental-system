// ======================
// KHAI BÁO BIẾN TOÀN CỤC
// ======================
var map;
var userMarker;
var searchMarker; // Đánh dấu vị trí tìm kiếm địa chỉ
var allMarkers = [];
var isUserAction = false;

const DEFAULT_LAT = 10.762622;
const DEFAULT_LNG = 106.660172;

// =================================
// 1. HÀM KHỞI TẠO BẢN ĐỒ (INIT MAP)
// =================================
function initMap(vehicleData) {
    map = L.map("map").setView([DEFAULT_LAT, DEFAULT_LNG], 12);

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap",
    }).addTo(map);

    function createCarIcon(color) {
        var svgHtml = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="35" height="35">
            <path fill="${color}" stroke="white" stroke-width="20" d="M112 112c0-26.5 21.5-48 48-48h192c26.5 0 48 21.5 48 48v288c0 26.5-21.5 48-48 48H160c-26.5 0-48-21.5-48-48V112z"/>
            <path fill="rgba(255,255,255,0.5)" d="M160 128h192v64H160z"/><circle cx="120" cy="144" r="20" fill="#333"/><circle cx="392" cy="144" r="20" fill="#333"/><circle cx="120" cy="368" r="20" fill="#333"/><circle cx="392" cy="368" r="20" fill="#333"/></svg>`;
        return L.divIcon({ className: "custom-car-icon", html: svgHtml, iconSize: [35, 35], iconAnchor: [17, 17], popupAnchor: [0, -10] });
    }

    const icons = {
        green: createCarIcon("#28a745"),
        blue: createCarIcon("#007bff"),
        red: createCarIcon("#dc3545"),
        yellow: createCarIcon("#ffc107")
    };

    getUserLocation(false);

    vehicleData.forEach(function (xe) {
        // --- LOGIC TRẠNG THÁI & ICON ---
        var rawStatus = xe.status ? xe.status.toString() : "Available";
        var statusNormal = rawStatus.toLowerCase().trim().replace(/_/g, " ");
        var bookingUrl = "/thue-xe/" + xe.id + "/";

        var iconObj = icons.green;
        var statusConfig = {
            label: "Sẵn sàng",
            color: "#28a745",
            btnText: "THUÊ NGAY",
            btnColor: "#28a745",
            isBookable: true,
            note: "✅ Xe đang rảnh, có thể nhận ngay!"
        };

        if (statusNormal === "maintenance" || statusNormal === "bao tri") {
            iconObj = icons.red;
            statusConfig = {
                label: "Bảo trì",
                color: "#dc3545",
                btnText: "ĐANG SỬA",
                btnColor: "#ccc",
                isBookable: false,
                note: "⚠️ Xe đang bảo dưỡng định kỳ."
            };
        } else if (statusNormal === "in operation" || statusNormal === "in_use" || statusNormal === "dang hoat dong") {
            iconObj = icons.blue;
            statusConfig = {
                label: "Đang hoạt động",
                color: "#007bff",
                btnText: "ĐẶT TRƯỚC",
                btnColor: "#007bff",
                isBookable: true,
                note: "🔵 Khách đang đi xe."
            };
        } else if (statusNormal === "booked" || statusNormal === "da dat") {
            iconObj = icons.yellow;
        }

        var marker = L.marker([xe.lat, xe.lng], { icon: iconObj }).addTo(map);
        marker.id = xe.id;
        marker.status = xe.status;
        allMarkers.push(marker);

        // --- NỘI DUNG POPUP ĐẦY ĐỦ THÔNG TIN ---
        var popupContent = `
            <div style="font-family: 'Segoe UI', Roboto, sans-serif; min-width: 250px; padding: 5px;">
                <h3 style="margin: 0 0 5px 0; font-size: 16px; color: #2c3e50; font-weight: 700;">${xe.name}</h3>
                <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                    <span style="background: #fff; border: 1px solid ${statusConfig.color}; color: ${statusConfig.color}; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 700;">
                        ${statusConfig.label}
                    </span>
                    <div style="font-size: 12px; color: #666;">
                        <span style="color: #f1c40f;">⭐</span> <b>${xe.rating || '4.8'}</b> (12)
                    </div>
                </div>
                <div style="background: #f8f9fa; padding: 10px; border-radius: 6px; margin-bottom: 10px; border-left: 4px solid ${statusConfig.color};">
                    <div style="color: #d63031; font-size: 18px; font-weight: bold; line-height: 1;">
                        ${parseInt(xe.price).toLocaleString("vi-VN")}đ 
                    </div>
                    <div style="font-size: 12px; color: #666; margin-top: 4px;">Giá thuê 1 ngày (24h)</div>
                </div>
                <div style="font-size: 11px; margin-bottom: 12px; padding: 5px; background: #f1f1f1; border-radius: 4px; color: #333;">
                    ${statusConfig.note}
                </div>
                <div style="display: flex; gap: 5px;">
                    <button onclick="openLocationModal('${xe.name}', ${xe.lat}, ${xe.lng})" style="flex: 1; cursor:pointer; background: #fff; color: #17a2b8; border: 1px solid #17a2b8; padding: 8px 0; border-radius: 4px; font-weight: 600; font-size: 13px;">📍 Vị trí</button>
                    <button onclick="openTermsModal('${xe.name}', ${xe.price})" style="flex: 1; cursor:pointer; background: #6c757d; color: white; border: none; padding: 8px 0; border-radius: 4px; font-weight: 600; font-size: 13px;">📄 HĐ</button>
                    <button onclick="${statusConfig.isBookable ? `window.location.href='${bookingUrl}'` : "return false;"}" style="flex: 2; cursor: pointer; background: ${statusConfig.btnColor}; color: white; border: none; padding: 8px 0; border-radius: 4px; font-weight: 600; font-size: 13px;">${statusConfig.btnText}</button>
                </div>
            </div>`;
        marker.bindPopup(popupContent);
    });
}

// =========================
// 2. LẤY VỊ TRÍ NGƯỜI DÙNG
// =========================
function getUserLocation(forceFly = false) {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(function (position) {
        var lat = position.coords.latitude;
        var lng = position.coords.longitude;
        if (userMarker) {
            userMarker.setLatLng([lat, lng]);
        } else {
            userMarker = L.marker([lat, lng], {
                icon: L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-violet.png',
                    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                    iconSize: [25, 41], iconAnchor: [12, 41]
                })
            }).addTo(map).bindPopup("Vị trí của bạn");
        }
        if (forceFly) map.flyTo([lat, lng], 15, { duration: 1.5 });
    });
}

// =====================================
// 3. XỬ LÝ SỰ KIỆN (TÌM KIẾM & BỘ LỌC)
// =====================================
document.addEventListener("DOMContentLoaded", function () {
    const dataScript = document.getElementById("vehicles-data");
    if (dataScript) {
        try {
            var vehicleData = JSON.parse(dataScript.textContent);
            if (typeof vehicleData === "string") vehicleData = JSON.parse(vehicleData);
            initMap(vehicleData);
        } catch (e) { console.error("Lỗi dữ liệu:", e); }
    }

    // A. FIX TÌM KIẾM: Nhạy hơn (KeyDown) và có dấu Marker ghim vị trí
    const searchInput = document.getElementById('location-search');
    if (searchInput) {
        L.DomEvent.disableClickPropagation(searchInput);
        L.DomEvent.disableScrollPropagation(searchInput);

        searchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const address = this.value;
                if (!address) return;

                fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.length > 0) {
                            const lat = parseFloat(data[0].lat);
                            const lon = parseFloat(data[0].lon);

                            if (searchMarker) map.removeLayer(searchMarker);
                            searchMarker = L.marker([lat, lon]).addTo(map)
                                .bindPopup(`<b>Vị trí tìm thấy:</b><br>${address}`).openPopup();

                            map.flyTo([lat, lon], 16, { duration: 1.5 });
                        } else {
                            alert("Không tìm thấy địa chỉ này!");
                        }
                    })
                    .catch(err => console.error("Lỗi tìm kiếm:", err));
            }
        });
    }

    // B. FIX LỌC XE: Đồng bộ màu nút & ẩn/hiện Marker + Sidebar Item
    document.addEventListener('click', function (e) {
        const filterBtn = e.target.closest('.filter-btn');
        if (filterBtn) {
            e.preventDefault();
            const filterValue = filterBtn.getAttribute('data-filter').toLowerCase().trim();

            // Cập nhật màu nút (Active: Xanh, Inactive: Xám)
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('bg-primary', 'text-white');
                btn.classList.add('bg-slate-100', 'text-slate-600');
            });
            filterBtn.classList.remove('bg-slate-100', 'text-slate-600');
            filterBtn.classList.add('bg-primary', 'text-white');

            // Lọc Marker và Danh sách Sidebar
            allMarkers.forEach(marker => {
                const vehicleStatus = (marker.status || "").toLowerCase().trim();
                const sidebarItem = document.querySelector(`.vehicle-item[data-id="${marker.id}"]`);

                if (filterValue === 'all' || vehicleStatus === filterValue) {
                    if (!map.hasLayer(marker)) map.addLayer(marker);
                    if (sidebarItem) sidebarItem.style.display = 'flex';
                } else {
                    if (map.hasLayer(marker)) map.removeLayer(marker);
                    if (sidebarItem) sidebarItem.style.display = 'none';
                }
            });
            return;
        }

        const gpsBtn = e.target.closest('#locate-me-btn');
        if (gpsBtn) {
            isUserAction = true;
            getUserLocation(true);
        }
    });
});

// Logic mở Modal tọa độ/vị trí (Cần định nghĩa trong template)
window.openLocationModal = function (name, lat, lng) {
    var modal = document.getElementById("locationModal");
    if (modal) {
        document.getElementById("loc-car-name").innerText = name;
        document.getElementById("btn-view-map").onclick = function () {
            modal.style.display = "none";
            map.flyTo([lat, lng], 18, { duration: 2.0 });
        };
        modal.style.display = "block";
    }
};