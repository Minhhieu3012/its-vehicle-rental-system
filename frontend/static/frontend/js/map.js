document.addEventListener('DOMContentLoaded', function () {
    const mapElement = document.getElementById('map');
    if (!mapElement) return;

    // 1. KHỞI TẠO BẢN ĐỒ (Mặc định Hà Nội)
    const map = L.map('map', {
        zoomControl: false
    }).setView([21.0285, 105.8542], 13);

    // Tile Layer (Giao diện Voyager hiện đại)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    // Điều chỉnh vị trí nút Zoom sang góc dưới bên phải
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    let markers = [];
    let userMarker = null; // Quản lý Marker của người dùng
    let userCircle = null; // Vòng tròn sai số định vị

    const dataScript = document.getElementById('vehicles-data');
    if (!dataScript) return;

    try {
        const vehicles = JSON.parse(dataScript.textContent);

        // 2. HÀM VẼ MARKER XE VÀ LỌC TRẠNG THÁI (ITS LOGIC)
        function renderMarkers(filterStatus = 'all') {
            // Xóa toàn bộ Marker xe cũ
            markers.forEach(m => map.removeLayer(m));
            markers = [];
            let count = 0;

            vehicles.forEach(v => {
                // Logic lọc trạng thái (không phân biệt hoa thường)
                if (filterStatus !== 'all' && v.status.toLowerCase() !== filterStatus.toLowerCase()) {
                    return;
                }

                // Đổi màu Marker: Available (Xanh) | Đã thuê/Đang đi (Đỏ)
                const markerColor = (v.status.toLowerCase() === 'available') ? '#0ea5e9' : '#ef4444';

                const carIcon = L.divIcon({
                    className: 'custom-map-icon',
                    html: `<div class="w-8 h-8 rounded-full flex items-center justify-center border-2 border-white shadow-lg" style="background-color: ${markerColor}">
                               <span class="material-symbols-outlined text-[18px] text-white">directions_car</span>
                           </div>`,
                    iconSize: [32, 32],
                    iconAnchor: [16, 32],
                    popupAnchor: [0, -32]
                });

                const marker = L.marker([v.lat, v.lng], { icon: carIcon }).addTo(map);

                // Nội dung Popup chi tiết khi click vào xe
                const popupContent = `
                    <div class="text-center min-w-[150px] p-2">
                        <img src="${v.image_url}" class="w-full h-20 object-cover rounded mb-2" onerror="this.src='/static/frontend/img/placeholder.jpg'">
                        <h3 class="font-bold text-slate-800">${v.name}</h3>
                        <p class="text-xs text-slate-500 mb-2">${v.price}đ/ngày</p>
                        <a href="${v.detail_url}" class="block bg-primary text-white text-xs font-bold py-2 rounded hover:bg-opacity-90 transition">
                            Xem chi tiết
                        </a>
                    </div>
                `;
                marker.bindPopup(popupContent);
                markers.push(marker);
                count++;
            });

            // Cập nhật số lượng xe hiển thị trên Sidebar
            const countElement = document.getElementById('vehicle-count');
            if (countElement) {
                countElement.innerText = `${count} xe tìm thấy`;
            }
        }

        // 3. XỬ LÝ SỰ KIỆN NÚT BẤM FILTER
        const filterButtons = document.querySelectorAll('.filter-btn');
        filterButtons.forEach(btn => {
            btn.addEventListener('click', function () {
                filterButtons.forEach(b => {
                    b.classList.remove('bg-primary', 'text-white');
                    b.classList.add('bg-slate-100', 'text-slate-600');
                });
                this.classList.remove('bg-slate-100', 'text-slate-600');
                this.classList.add('bg-primary', 'text-white');

                renderMarkers(this.getAttribute('data-filter'));
            });
        });

        // Khởi tạo xe lần đầu
        renderMarkers();

    } catch (e) {
        console.error("Lỗi phân tích dữ liệu bản đồ:", e);
    }

    // 4. LOGIC ĐỊNH VỊ CHÍNH XÁC CAO (GPS)
    const locateBtn = document.getElementById('locate-me');
    if (locateBtn) {
        locateBtn.addEventListener('click', () => {
            // Hiệu ứng đang tìm kiếm
            locateBtn.classList.add('animate-pulse', 'text-primary');

            map.locate({
                setView: true,
                maxZoom: 17, // Phóng to sâu để thấy rõ đường phố
                enableHighAccuracy: true // Ép sử dụng GPS chính xác cao
            });
        });
    }

    // Sự kiện khi GPS tìm thấy vị trí thực tế
    map.on('locationfound', function (e) {
        if (userMarker) map.removeLayer(userMarker);
        if (userCircle) map.removeLayer(userCircle);

        // Tạo User Marker với hiệu ứng sóng lan tỏa (Ping)
        const userIcon = L.divIcon({
            className: 'user-location',
            html: `<div class="relative flex items-center justify-center">
                    <div class="absolute w-8 h-8 bg-blue-500 rounded-full animate-ping opacity-30"></div>
                    <div class="relative w-4 h-4 bg-blue-600 border-2 border-white rounded-full shadow-lg"></div>
                   </div>`,
            iconSize: [32, 32]
        });

        userMarker = L.marker(e.latlng, { icon: userIcon }).addTo(map)
            .bindPopup("Vị trí chính xác của bạn").openPopup();

        // Vẽ vòng tròn độ sai số
        userCircle = L.circle(e.latlng, e.accuracy, {
            color: '#3b82f6',
            fillColor: '#3b82f6',
            fillOpacity: 0.1,
            weight: 1
        }).addTo(map);

        locateBtn.classList.remove('animate-pulse', 'text-primary');
    });

    map.on('locationerror', function () {
        alert("Không thể lấy vị trí. Vui lòng bật GPS và cho phép quyền truy cập vị trí.");
        locateBtn.classList.remove('animate-pulse', 'text-primary');
    });

    // 5. TÌM KIẾM VỊ TRÍ QUA Ô NHẬP LIỆU (Nominatim API)
    const searchInput = document.getElementById('location-search');
    if (searchInput) {
        searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                const query = this.value;
                if (!query) return;

                fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${query}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.length > 0) {
                            const loc = data[0];
                            map.setView([loc.lat, loc.lon], 16);
                            L.marker([loc.lat, loc.lon])
                                .addTo(map)
                                .bindPopup(`<b>Kết quả:</b> ${query}`)
                                .openPopup();
                        } else {
                            alert("Không tìm thấy địa điểm này!");
                        }
                    })
                    .catch(err => console.error("Lỗi tìm kiếm:", err));
            }
        });
    }
});