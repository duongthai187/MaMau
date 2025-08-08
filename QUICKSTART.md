# 🚀 Quick Start Guide - Real-time Pricing

## ⚡ **Cách 1: CRUD Only (Không cần Kafka)**

Nếu bạn chỉ cần tính năng CRUD:

```bash
# 1. Cài dependencies
pip install -r requirements.txt

# 2. Chạy app
python run_fastapi.py
```

✅ **Truy cập**: http://localhost:5000

---

## 📊 **Cách 2: CRUD + Real-time Pricing (Cần Kafka)**

### Bước 1: Start Kafka Server

```bash
# Sử dụng Docker (Khuyến nghị)
docker-compose up -d

# Kiểm tra
docker-compose ps
```

**Kết quả mong đợi:**
```
NAME        IMAGE                             STATUS
kafka       confluentinc/cp-kafka:7.4.0       Up
zookeeper   confluentinc/cp-zookeeper:7.4.0   Up  
kafka-ui    provectuslabs/kafka-ui:latest     Up
```

### Bước 2: Start Data Producer

**Terminal mới:**
```bash
python kafka_producer.py
```

**Output mong đợi:**
```
✅ Connected to Kafka successfully
📈 Published rate update: gold = 75,500,000 VND  
📈 Published rate update: silver = 850,000 VND
⚖️  Published weights: RING_GOLD_001 = 5.2g gold
📊 Batch 1 completed
```

### Bước 3: Start FastAPI App

**Terminal mới:**
```bash
python run_fastapi.py
```

**Output mong đợi:**
```
Kafka pricing consumer started successfully
INFO:     Application startup complete.
```

### Bước 4: Test Real-time Updates

1. **Truy cập**: http://localhost:5000/pricing
2. **Mở Browser DevTools** → Network → Event Stream
3. **Quan sát**: Real-time pricing updates từ producer

---

## 🛠️ **Troubleshooting**

### ❌ Lỗi: "Could not start Kafka consumer"
**Nguyên nhân**: Chưa có Kafka server
**Giải pháp**: 
- Chạy `docker-compose up -d` trước
- Hoặc bỏ qua - app vẫn chạy được CRUD

### ❌ Lỗi: "Cannot connect to Kafka" 
**Nguyên nhân**: Port 9092 bị occupied
**Giải pháp**:
```bash
# Stop các container cũ
docker-compose down

# Restart
docker-compose up -d
```

### ❌ Lỗi: Docker không tìm thấy
**Giải pháp**: Cài Docker Desktop từ https://docker.com

---

## 📋 **Useful Commands**

```bash
# Xem Kafka topics
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Xem messages trong topic
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic rates --from-beginning

# Stop everything
docker-compose down
```

---

## 🎯 **URLs Quan trọng**

- **FastAPI App**: http://localhost:5000
- **API Docs**: http://localhost:5000/docs  
- **Real-time Pricing**: http://localhost:5000/pricing
- **Kafka UI**: http://localhost:8080
- **Health Check**: http://localhost:5000/health

---

## ✅ **Success Indicators**

### CRUD Working:
- ✅ Vào http://localhost:5000 thấy UI
- ✅ Click "Products" có danh sách
- ✅ API docs ở /docs hoạt động

### Real-time Pricing Working:
- ✅ Producer bắn data liên tục
- ✅ /pricing page nhận updates  
- ✅ /health show kafka_connected: true
- ✅ SSE connections > 0 when viewing /pricing

**🎉 Success! Enjoy your real-time pricing system!**
