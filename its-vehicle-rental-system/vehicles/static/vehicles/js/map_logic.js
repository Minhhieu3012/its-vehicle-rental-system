// ======================
// KHAI BÁO BIẾN TOÀN CỤC
// ======================
var map;
var userMarker;
var currentRoute = null;
var allMarkers = []; // Lưu trữ để phục vụ logic lọc xe

var userLat = null;
var userLng = null;

// Tọa độ mặc định (TP.HCM)
const DEFAULT_LAT = 10.762622;
const DEFAULT_LNG = 106.660172;

// =================================
// 1. HÀM KHỞI TẠO BẢN ĐỒ (INIT MAP)
// =================================
function initMap(vehicleData) {
    // Dùng tọa độ mặc định
    map = L.map("map").setView([DEFAULT_LAT, DEFAULT_LNG], 12);

    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap",
    }).addTo(map);

    // Định nghĩa Icon Xe
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

    const icons = {
        green: createCarIcon("#28a745"),
        yellow: createCarIcon("#ffc107"),
        blue: createCarIcon("#007bff"),
        red: createCarIcon("#dc3545")
    };

    // Gọi hàm lấy vị trí thật
    getUserLocation();

    // Vẽ các xe lên bản đồ và lưu vào mảng markers để lọc
    vehicleData.forEach(function (xe) {
        var rawStatus = xe.status ? xe.status.toString() : "available";
        var statusNormal = rawStatus.toLowerCase().trim().replace(/_/g, " ");
        var bookingUrl = "/booking/create/" + xe.id + "/";

        var statusConfig = {
            label: "Sẵn sàng",
            color: "#28a745",
            icon: icons.green,
            btnText: "THUÊ NGAY",
            btnColor: "#28a745",
            isBookable: true,
            note: "✅ Xe đang rảnh, có thể nhận ngay!",
        };

        if (statusNormal === "maintenance" || statusNormal === "bao tri") {
            statusConfig = {
                label: "Bảo trì",
                color: "#dc3545",
                icon: icons.red,
                btnText: "ĐANG SỬA",
                btnColor: "#ccc",
                isBookable: false,
                note: "⚠️ Xe đang bảo dưỡng định kỳ.",
            };
        } else if (statusNormal === "in operation" || statusNormal === "dang hoat dong") {
            var returnTime = new Date();
            returnTime.setHours(returnTime.getHours() + 4);
            var timeStr = returnTime.getHours() + ":00 hôm nay";
            statusConfig = {
                label: "Đang hoạt động",
                color: "#007bff",
                icon: icons.blue,
                btnText: "ĐẶT TRƯỚC",
                btnColor: "#007bff",
                isBookable: true,
                note: `🔵 Khách đang đi. Trả xe lúc <b>${timeStr}</b>`,
            };
        } else if (statusNormal === "booked" || statusNormal === "da dat") {
            var today = new Date();
            var endDate = new Date(today);
            endDate.setDate(today.getDate() + 3);
            var dateStr = `${today.getDate()}/${today.getMonth() + 1} - ${endDate.getDate()}/${endDate.getMonth() + 1}`;
            statusConfig = {
                label: "Đã có khách",
                color: "#ffc107",
                icon: icons.yellow,
                btnText: "ĐẶT LỊCH",
                btnColor: "#fd7e14",
                isBookable: true,
                note: `🟡 Đã kín lịch: <b>${dateStr}</b>`,
            };
        }

        var marker = L.marker([xe.lat, xe.lng], { icon: statusConfig.icon }).addTo(map);

        // Gán thuộc tính status vào marker để phục vụ việc lọc
        marker.status = xe.status;
        allMarkers.push(marker);

        var popupContent = `
            <div style="font-family: 'Segoe UI', Roboto, sans-serif; min-width: 250px; padding: 5px;">
                <h3 style="margin: 0 0 5px 0; font-size: 16px; color: #2c3e50; font-weight: 700;">${xe.name}</h3>
                <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                    <span style="background: #fff; border: 1px solid ${statusConfig.color}; color: ${statusConfig.color}; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 700;">
                        ${statusConfig.label}
                    </span>
                    <div style="font-size: 12px; color: #666;">
                        <span style="color: #f1c40f;">⭐</span> <b>${xe.rating}</b> (${xe.trips})
                    </div>
                </div>
                <div style="background: #f8f9fa; padding: 10px; border-radius: 6px; margin-bottom: 10px; border-left: 4px solid ${statusConfig.color};">
                    <div style="color: #d63031; font-size: 18px; font-weight: bold; line-height: 1;">
                        ${parseInt(xe.price).toLocaleString("vi-VN")}đ 
                    </div>
                    <div style="font-size: 12px; color: #666; margin-top: 4px;">Giá thuê 1 ngày (24h)</div>
                </div>
                <div style="font-size: 12px; margin-bottom: 12px; padding: 5px; background: #f1f1f1; border-radius: 4px; color: #333;">
                    ${statusConfig.note}
                </div>
                <div style="display: flex; gap: 5px;">
                    <button onclick="openLocationModal('${xe.name}', ${xe.lat}, ${xe.lng})" style="flex: 1; cursor:pointer; background: #fff; color: #17a2b8; border: 1px solid #17a2b8; padding: 8px 0; border-radius: 4px; font-weight: 600; font-size: 13px;">📍 Vị trí</button>
                    <button onclick="openTermsModal('${xe.name}', ${xe.price})" style="flex: 1; cursor:pointer; background: #6c757d; color: white; border: none; padding: 8px 0; border-radius: 4px; font-weight: 600; font-size: 13px;">📄 HĐ</button>
                    <button onclick="${statusConfig.isBookable ? `window.location.href='${bookingUrl}'` : "return false;"}" style="flex: 2; cursor: ${statusConfig.isBookable ? "pointer" : "not-allowed"}; background: ${statusConfig.btnColor}; color: white; border: none; padding: 8px 0; border-radius: 4px; font-weight: 600; font-size: 13px;">${statusConfig.btnText}</button>
                </div>
            </div>
        `;
        marker.bindPopup(popupContent);
    });
}

// =========================
// 2. LẤY VỊ TRÍ NGƯỜI DÙNG
// =========================
function getUserLocation() {
    if (!navigator.geolocation) {
        alert("Trình duyệt không hỗ trợ GPS.");
        return;
    }
    navigator.geolocation.getCurrentPosition(
        function (position) {
            userLat = position.coords.latitude;
            userLng = position.coords.longitude;

            const userIcon = L.icon({
                iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-violet.png",
                shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41],
            });

            if (userMarker) {
                userMarker.setLatLng([userLat, userLng]);
            } else {
                userMarker = L.marker([userLat, userLng], { icon: userIcon })
                    .addTo(map)
                    .bindPopup("<b>Bạn đang ở đây!</b>");
            }

            // Nhảy về vị trí người dùng
            map.flyTo([userLat, userLng], 15, { duration: 1.5 });
            userMarker.openPopup();
        },
        function (error) {
            alert("Lỗi GPS: Vui lòng bật vị trí và cho phép trình duyệt truy cập.");
            console.warn("Lỗi GPS:", error.message);
        }
    );
}

// ===================================
// 3. TÍNH TOÁN LỘ TRÌNH & DỊCH THUẬT
// ===================================
window.calculateRoute = function (destLat, destLng) {
    if (userLat === null || userLng === null) {
        alert("Đang tìm vị trí của bạn... Vui lòng bật GPS và thử lại sau giây lát.");
        getUserLocation();
        return;
    }

    var summaryBox = document.getElementById("route-summary");
    var instructionList = document.getElementById("route-instructions");
    if (summaryBox && instructionList) {
        summaryBox.innerHTML = '<div style="text-align:center; padding: 20px; color: #666;">⏳ Đang tìm đường...</div>';
        instructionList.innerHTML = "";
        openModal();
    }

    if (currentRoute) map.removeControl(currentRoute);

    currentRoute = L.Routing.control({
        waypoints: [L.latLng(userLat, userLng), L.latLng(destLat, destLng)],
        routeWhileDragging: false,
        showAlternatives: false,
        show: false,
        lineOptions: { styles: [{ color: "#007bff", opacity: 0.7, weight: 6 }] },
        createMarker: function () { return null; },
    })
        .on("routesfound", function (e) {
            var route = e.routes[0];
            var summary = route.summary;
            var distanceInKm = (summary.totalDistance / 1000).toFixed(2);
            var timeInMinutes = Math.round(summary.totalTime / 60);
            var shipCost = Math.round(distanceInKm * 30000).toLocaleString("vi-VN");

            var summaryHTML = `
            <div style="font-family: 'Segoe UI', sans-serif;">
                <div style="margin-bottom: 8px; display: flex; align-items: center;">
                    <span style="font-size: 20px; margin-right: 10px;">🏁</span> 
                    <div><div style="font-size: 13px; color: #666;">Quãng đường</div><strong style="font-size: 16px;">${distanceInKm} km</strong></div>
                </div>
                <div style="margin-bottom: 8px; display: flex; align-items: center;">
                    <span style="font-size: 20px; margin-right: 10px;">⏳</span> 
                    <div><div style="font-size: 13px; color: #666;">Thời gian</div><strong style="font-size: 16px;">${timeInMinutes} phút</strong></div>
                </div>
                <div style="margin-top: 12px; padding-top: 10px; border-top: 1px dashed #ccc; display: flex; align-items: center;">
                    <span style="font-size: 20px; margin-right: 10px;">🚚</span> 
                    <div><div style="font-size: 13px; color: #666;">Phí giao xe (30k/km)</div><strong style="font-size: 18px; color: #d63031;">${shipCost}đ</strong></div>
                </div>
            </div>
        `;
            document.getElementById("route-summary").innerHTML = summaryHTML;

            var instructions = route.instructions;
            var listHTML = "";

            instructions.forEach(function (step) {
                var icon = "⬆️";
                var text = step.text;

                var translatedText = text
                    .replace(/Enter (.*?) and take the (\d+)(?:st|nd|rd|th) exit/gi, "Vào $1 và đi theo lối ra thứ $2")
                    .replace(/Enter (.*?) and take the exit/gi, "Vào $1 và đi theo lối ra")
                    .replace(/Exit the (?:traffic circle|roundabout)/gi, "Ra khỏi vòng xoay")
                    .replace(/Into the (?:traffic circle|roundabout)/gi, "Vào vòng xoay")
                    .replace(/Make a U-turn/gi, "Quay đầu xe")
                    .replace(/Make a (?:sharp|slight) right/gi, "Cua sang phải")
                    .replace(/Make a (?:sharp|slight) left/gi, "Cua sang trái")
                    .replace(/Make a right/gi, "Rẽ phải")
                    .replace(/Make a left/gi, "Rẽ trái")
                    .replace(/Turn left/gi, "Rẽ trái")
                    .replace(/Turn right/gi, "Rẽ phải")
                    .replace(/Keep left/gi, "Đi sang làn trái")
                    .replace(/Keep right/gi, "Đi sang làn phải")
                    .replace(/Go straight/gi, "Đi thẳng")
                    .replace(/Take the ramp/gi, "Đi vào đường dẫn")
                    .replace(/slightly left/gi, "chếch sang trái")
                    .replace(/slightly right/gi, "chếch sang phải")
                    .replace(/sharp left/gi, "ngoặt gấp sang trái")
                    .replace(/sharp right/gi, "ngoặt gấp sang phải")
                    .replace(/towards/gi, "về hướng")
                    .replace(/stay on/gi, "tiếp tục đi trên")
                    .replace(/ and /gi, " và ")
                    .replace(/ onto /gi, " vào đường ")
                    .replace(/ on /gi, " trên đường ")
                    .replace(/ to /gi, " đến ")
                    .replace(/ at /gi, " tại ")
                    .replace(/ your /gi, " của bạn ")
                    .replace(/\bNorth\b/gi, "Bắc")
                    .replace(/\bSouth\b/gi, "Nam")
                    .replace(/\bEast\b/gi, "Đông")
                    .replace(/\bWest\b/gi, "Tây")
                    .replace(/\bNortheast\b/gi, "Đông Bắc")
                    .replace(/\bNorthwest\b/gi, "Tây Bắc")
                    .replace(/\bSoutheast\b/gi, "Đông Nam")
                    .replace(/\bSouthwest\b/gi, "Tây Nam")
                    .replace(/Enter /gi, "Đi vào ")
                    .replace(/Head /gi, "Đi về hướng ")
                    .replace(/Continue/gi, "Tiếp tục đi")
                    .replace(/Arrive at/gi, "Đến")
                    .replace(/You have arrived/gi, "Bạn đã đến nơi")
                    .replace(/destination/gi, "điểm đến")
                    .replace(/\bright\b/gi, "bên phải")
                    .replace(/\bleft\b/gi, "bên trái")
                    .replace(/\s+/g, " ")
                    .trim();

                if (text.match(/Left|left/)) icon = "⬅️";
                if (text.match(/Right|right/)) icon = "➡️";
                if (text.match(/U-turn/)) icon = "↩️";
                if (text.match(/roundabout|circle/)) icon = "🔄";
                if (text.match(/Arrive|destination/)) icon = "🎯";

                listHTML += `
                <li style="padding: 10px 0; border-bottom: 1px solid #eee; display: flex; align-items: start;">
                    <span style="font-size: 20px; margin-right: 10px; min-width: 25px;">${icon}</span>
                    <div><div style="font-weight: 500; color: #333;">${translatedText}</div><small style="color: #888;">${step.distance > 0 ? Math.round(step.distance) + " mét" : ""}</small></div>
                </li>
            `;
            });
            document.getElementById("route-instructions").innerHTML = listHTML;
        })
        .on("routingerror", function (e) {
            document.getElementById("route-summary").innerHTML = '<div style="color: red;">❌ Không tìm thấy đường đi.</div>';
        })
        .addTo(map);
};

// =================
// 4. QUẢN LÝ MODAL
// =================
window.openModal = function () {
    var modal = document.getElementById("routeModal");
    if (modal) modal.style.display = "block";
};

window.closeModal = function () {
    var modal = document.getElementById("routeModal");
    if (modal) modal.style.display = "none";
};

window.openTermsModal = function (name, price) {
    var modal = document.getElementById("termsModal");
    if (modal) {
        document.getElementById("term-car-name").innerText = name;
        var priceFormatted = parseInt(price).toLocaleString("vi-VN");
        document.getElementById("term-car-price").innerText = priceFormatted + "đ/ngày";
        modal.style.display = "block";
    }
};

window.closeTermsModal = function () {
    var modal = document.getElementById("termsModal");
    if (modal) modal.style.display = "none";
};

window.openLocationModal = function (name, lat, lng) {
    var modal = document.getElementById("locationModal");
    if (modal) {
        document.getElementById("loc-car-name").innerText = name;
        document.getElementById("btn-view-map").onclick = function () {
            modal.style.display = "none";
            map.flyTo([lat, lng], 18, { duration: 2.0 });
        };
        document.getElementById("btn-start-route").onclick = function () {
            modal.style.display = "none";
            calculateRoute(lat, lng);
        };
        modal.style.display = "block";
    }
};

window.closeLocationModal = function () {
    var modal = document.getElementById("locationModal");
    if (modal) modal.style.display = "none";
};

// Đóng modal khi click ra ngoài
window.onclick = function (event) {
    var mRoute = document.getElementById("routeModal");
    var mTerms = document.getElementById("termsModal");
    var mLoc = document.getElementById("locationModal");
    if (event.target == mRoute) mRoute.style.display = "none";
    if (event.target == mTerms) mTerms.style.display = "none";
    if (event.target == mLoc) mLoc.style.display = "none";
};

// =====================================
// 5. TỰ ĐỘNG KHỞI TẠO & XỬ LÝ SỰ KIỆN (FIXED)
// =====================================
document.addEventListener("DOMContentLoaded", function () {
    const dataScript = document.getElementById("vehicles-data");

    if (dataScript) {
        try {
            var vehicleData = JSON.parse(dataScript.textContent);

            if (typeof vehicleData === "string") {
                vehicleData = JSON.parse(vehicleData);
            }

            console.log("Dữ liệu xe chuẩn:", vehicleData);

            if (Array.isArray(vehicleData)) {
                initMap(vehicleData);
            } else {
                console.error("Lỗi: Dữ liệu xe không đúng định dạng danh sách.");
            }
        } catch (error) {
            console.error("Lỗi khi đọc dữ liệu xe:", error);
        }
    } else {
        console.warn("Không tìm thấy dữ liệu xe (ID: vehicles-data)");
    }

    // A. XỬ LÝ TÌM KIẾM ĐỊA CHỈ (FIXED: Dùng Fetch trực tiếp tránh lỗi Geocoder plugin)
    const searchInput = document.getElementById('location-search');
    if (searchInput) {
        searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const address = this.value;
                if (!address) return;

                fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.length > 0) {
                            map.flyTo([data[0].lat, data[0].lon], 15);
                            L.popup().setLatLng([data[0].lat, data[0].lon]).setContent(address).openOn(map);
                        } else { alert("Không tìm thấy địa chỉ!"); }
                    })
                    .catch(err => console.error("Lỗi Geocoding:", err));
            }
        });
    }

    // B. XỬ LÝ CÁC NÚT BỘ LỌC (Sử dụng Event Delegation bền bỉ hơn)
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.filter-btn');
        if (btn) {
            const filterValue = btn.getAttribute('data-filter');

            // Cập nhật UI nút bấm
            document.querySelectorAll('.filter-btn').forEach(b => {
                b.classList.remove('bg-primary', 'text-white');
                b.classList.add('bg-slate-100', 'text-slate-600');
            });
            btn.classList.replace('bg-slate-100', 'bg-primary');
            btn.classList.replace('text-slate-600', 'text-white');

            // Lọc Marker trên bản đồ
            allMarkers.forEach(marker => {
                // Chuẩn hóa status để so sánh chính xác
                const mStatus = (marker.status || "").toLowerCase().trim();
                const fValue = filterValue.toLowerCase().trim();

                if (fValue === 'all' || mStatus === fValue) {
                    map.addLayer(marker);
                } else {
                    map.removeLayer(marker);
                }
            });
        }

        // C. NÚT GPS (FIXED: Tích hợp vào Event Delegation)
        const gpsBtn = e.target.closest('#locate-me-btn');
        if (gpsBtn) {
            e.preventDefault();
            getUserLocation();
        }
    });
});