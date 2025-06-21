# دليل النشر

## المتطلبات

### البرمجيات
- Docker 24.0+
- Docker Compose 2.0+
- Kubernetes 1.25+ (للنشر على السحابة)
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Elasticsearch 8.10+

### الموارد
- وحدة معالجة مركزية: 4 أنوية كحد أدنى
- ذاكرة: 8GB كحد أدنى
- مساحة تخزين: 50GB كحد أدنى

## النشر المحلي

### 1. إعداد البيئة
```bash
# استنساخ المستودع
git clone https://github.com/your-org/medical-platform.git
cd medical-platform

# إنشاء ملف البيئة
cp .env.example .env
nano .env  # تعديل المتغيرات حسب الحاجة
```

### 2. تشغيل مع Docker Compose
```bash
# بناء وتشغيل الخدمات
docker-compose -f docker/docker-compose.yml up -d

# مراقبة السجلات
docker-compose -f docker/docker-compose.yml logs -f

# تنفيذ ترحيلات قاعدة البيانات
docker-compose -f docker/docker-compose.yml exec api alembic upgrade head
```

### 3. التحقق من الصحة
```bash
# فحص صحة الخدمات
curl http://localhost/health

# فحص السجلات
docker-compose -f docker/docker-compose.yml logs api
```

## النشر على الإنتاج

### 1. إعداد البنية التحتية

#### AWS
```bash
# تثبيت AWS CLI
pip install awscli

# تكوين AWS
aws configure

# إنشاء مجموعة EKS
eksctl create cluster -f k8s/cluster.yaml
```

#### Google Cloud
```bash
# تثبيت Google Cloud SDK
# تكوين GCloud
gcloud init
gcloud container clusters create medical-cluster
```

### 2. نشر السر والتكوينات
```bash
# إنشاء مساحة الأسماء
kubectl apply -f k8s/namespace.yaml

# إنشاء السر
kubectl create secret generic app-secrets \
    --from-file=.env \
    --namespace=medical-platform

# تطبيق ConfigMaps
kubectl apply -f k8s/configmap.yaml
```

### 3. نشر الخدمات
```bash
# نشر قاعدة البيانات
kubectl apply -f k8s/database/

# نشر Redis
kubectl apply -f k8s/redis/

# نشر Elasticsearch
kubectl apply -f k8s/elasticsearch/

# نشر API
kubectl apply -f k8s/api/

# نشر Nginx
kubectl apply -f k8s/nginx/
```

### 4. تكوين DNS وشهادات SSL
```bash
# تثبيت cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.7.0/cert-manager.yaml

# تكوين المُصدر
kubectl apply -f k8s/cert-issuer.yaml

# تطبيق Ingress
kubectl apply -f k8s/ingress.yaml
```

## المراقبة والصيانة

### 1. إعداد المراقبة
```bash
# نشر Prometheus
kubectl apply -f k8s/prometheus/

# نشر Grafana
kubectl apply -f k8s/grafana/

# تكوين التنبيهات
kubectl apply -f k8s/alerts/
```

### 2. النسخ الاحتياطي
```bash
# نسخ احتياطي لقاعدة البيانات
kubectl exec -it $(kubectl get pod -l app=postgres -o jsonpath="{.items[0].metadata.name}") -- \
    pg_dump -U postgres medical_db > backup.sql

# نسخ احتياطي لـ Redis
kubectl exec -it $(kubectl get pod -l app=redis -o jsonpath="{.items[0].metadata.name}") -- \
    redis-cli SAVE
```

### 3. استعادة النسخ الاحتياطي
```bash
# استعادة قاعدة البيانات
cat backup.sql | kubectl exec -i $(kubectl get pod -l app=postgres -o jsonpath="{.items[0].metadata.name}") -- \
    psql -U postgres medical_db
```

## التحديثات والترقيات

### 1. تحديث التطبيق
```bash
# تحديث صورة Docker
docker build -t medical-platform:new .
docker push medical-platform:new

# تحديث النشر
kubectl set image deployment/api api=medical-platform:new
```

### 2. ترقية البنية التحتية
```bash
# ترقية Kubernetes
kubectl apply -f k8s/upgrade/

# ترقية قاعدة البيانات
kubectl apply -f k8s/database/upgrade/
```

## استكشاف الأخطاء وإصلاحها

### 1. فحص السجلات
```bash
# سجلات API
kubectl logs -f deployment/api

# سجلات Nginx
kubectl logs -f deployment/nginx
```

### 2. فحص الأداء
```bash
# مقاييس الموارد
kubectl top pods
kubectl top nodes

# تتبع الشبكة
kubectl exec -it $(kubectl get pod -l app=api -o jsonpath="{.items[0].metadata.name}") -- \
    tcpdump -i any
```

### 3. اختبار الاتصال
```bash
# فحص الخدمات
kubectl exec -it debugger -- curl http://api:8000/health
kubectl exec -it debugger -- redis-cli -h redis ping
```

## قائمة التحقق قبل الإنتاج

### الأمان
- [ ] تحديث جميع الحزم
- [ ] مراجعة صلاحيات RBAC
- [ ] تفعيل جدار الحماية
- [ ] تكوين SSL/TLS

### الأداء
- [ ] ضبط موارد Kubernetes
- [ ] تكوين التخزين المؤقت
- [ ] ضبط قاعدة البيانات

### المراقبة
- [ ] تكوين التنبيهات
- [ ] إعداد لوحات المراقبة
- [ ] تفعيل تتبع الأداء

### النسخ الاحتياطي
- [ ] جدولة النسخ الاحتياطي
- [ ] اختبار الاستعادة
- [ ] تكوين التخزين الدائم
