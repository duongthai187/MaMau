/**
 * Real-time Pricing Client với SSE và local caching
 */
class PricingClient {
    constructor(baseUrl = '', options = {}) {
        this.baseUrl = baseUrl;
        this.options = {
            reconnectInterval: 5000, // 5 seconds
            maxReconnectAttempts: 10,
            cacheExpiryMs: 300000, // 5 minutes
            ...options
        };
        
        // Local pricing cache
        this.pricingCache = new Map();
        this.eventSource = null;
        this.reconnectAttempts = 0;
        this.isConnected = false;
        
        // Event callbacks
        this.onPricingUpdate = null;
        this.onConnectionChange = null;
        this.onError = null;
        
        // Auto-start connection
        this.connect();
    }
    
    /**
     * Kết nối SSE stream
     */
    connect() {
        if (this.eventSource) {
            this.disconnect();
        }
        
        console.log('Connecting to pricing stream...');
        
        this.eventSource = new EventSource(`${this.baseUrl}/events/pricing`);
        
        this.eventSource.onopen = () => {
            console.log('Connected to pricing stream');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            
            if (this.onConnectionChange) {
                this.onConnectionChange(true);
            }
        };
        
        this.eventSource.addEventListener('initial', (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('Received initial pricing data:', Object.keys(data.pricing).length, 'products');
                
                // Load initial data vào cache
                for (const [sku, pricing] of Object.entries(data.pricing)) {
                    this.updatePricingCache(sku, pricing);
                }
                
                if (this.onPricingUpdate) {
                    this.onPricingUpdate('initial', data.pricing);
                }
            } catch (error) {
                console.error('Error parsing initial data:', error);
            }
        });
        
        this.eventSource.addEventListener('pricing_update', (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('Pricing update for:', data.sku);
                
                this.updatePricingCache(data.sku, data.pricing);
                
                if (this.onPricingUpdate) {
                    this.onPricingUpdate('update', {[data.sku]: data.pricing});
                }
            } catch (error) {
                console.error('Error parsing pricing update:', error);
            }
        });
        
        this.eventSource.addEventListener('keepalive', (event) => {
            // Just for connection health
            console.log('Received keepalive');
        });
        
        this.eventSource.onerror = (error) => {
            console.error('SSE error:', error);
            this.isConnected = false;
            
            if (this.onConnectionChange) {
                this.onConnectionChange(false);
            }
            
            if (this.onError) {
                this.onError(error);
            }
            
            // Auto-reconnect
            this.scheduleReconnect();
        };
    }
    
    /**
     * Ngắt kết nối SSE
     */
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        this.isConnected = false;
        
        if (this.onConnectionChange) {
            this.onConnectionChange(false);
        }
    }
    
    /**
     * Schedule reconnect với exponential backoff
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
            console.error('Max reconnect attempts reached');
            if (this.onError) {
                this.onError(new Error('Max reconnect attempts reached'));
            }
            return;
        }
        
        const delay = Math.min(
            this.options.reconnectInterval * Math.pow(2, this.reconnectAttempts),
            30000 // Max 30 seconds
        );
        
        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);
        
        setTimeout(() => {
            this.reconnectAttempts++;
            this.connect();
        }, delay);
    }
    
    /**
     * Update pricing cache
     */
    updatePricingCache(sku, pricing) {
        this.pricingCache.set(sku, {
            ...pricing,
            cachedAt: Date.now(),
            as_of: new Date(pricing.as_of)
        });
    }
    
    /**
     * Lấy giá từ cache hoặc server
     */
    async getPricing(sku, strategy = 'freeze') {
        // Kiểm tra cache trước
        const cached = this.pricingCache.get(sku);
        if (cached && this.isPricingValid(cached)) {
            return {
                success: true,
                data: cached,
                source: 'cache'
            };
        }
        
        // Fallback to REST API
        try {
            const response = await fetch(`${this.baseUrl}/api/pricing/${sku}?strategy=${strategy}`);
            const result = await response.json();
            
            if (result.success) {
                this.updatePricingCache(sku, result.data);
            }
            
            return {
                ...result,
                source: 'api'
            };
        } catch (error) {
            console.error('Error fetching pricing:', error);
            
            // Nếu có cached data dù hết hạn, dùng strategy
            if (cached) {
                return this.applyOfflineStrategy(sku, cached, strategy);
            }
            
            return {
                success: false,
                error: error.message,
                source: 'error'
            };
        }
    }
    
    /**
     * Lấy tất cả giá từ cache
     */
    getAllPricing() {
        const result = {};
        for (const [sku, pricing] of this.pricingCache.entries()) {
            result[sku] = pricing;
        }
        return result;
    }
    
    /**
     * Kiểm tra pricing có valid không
     */
    isPricingValid(pricing) {
        if (!pricing || !pricing.as_of) return false;
        
        const now = Date.now();
        const asOf = pricing.as_of instanceof Date ? pricing.as_of.getTime() : new Date(pricing.as_of).getTime();
        const ttlMs = (pricing.ttl_sec || 300) * 1000;
        
        return (now - asOf) <= ttlMs;
    }
    
    /**
     * Apply offline strategy khi pricing hết hạn
     */
    applyOfflineStrategy(sku, pricing, strategy) {
        switch (strategy) {
            case 'deny':
                return {
                    success: false,
                    error: `Pricing data expired for ${sku}`,
                    data: pricing,
                    strategy_applied: 'deny',
                    source: 'cache_expired'
                };
                
            case 'surcharge':
                const surchargedPricing = {
                    ...pricing,
                    final_price: pricing.final_price * 1.05 // 5% surcharge
                };
                return {
                    success: true,
                    data: surchargedPricing,
                    strategy_applied: 'surcharge',
                    source: 'cache_surcharge',
                    is_expired: true
                };
                
            case 'freeze':
            default:
                return {
                    success: true,
                    data: pricing,
                    strategy_applied: 'freeze',
                    source: 'cache_freeze',
                    is_expired: true
                };
        }
    }
    
    /**
     * Format giá thành chuỗi VND
     */
    formatPrice(price) {
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(price);
    }
    
    /**
     * Lấy connection status
     */
    getConnectionStatus() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            cacheSize: this.pricingCache.size,
            validPricingCount: Array.from(this.pricingCache.values())
                .filter(p => this.isPricingValid(p)).length
        };
    }
    
    /**
     * Clear cache
     */
    clearCache() {
        this.pricingCache.clear();
        console.log('Pricing cache cleared');
    }
    
    /**
     * Trigger manual test update
     */
    async triggerTestUpdate() {
        try {
            const response = await fetch(`${this.baseUrl}/test/publish`, {
                method: 'POST'
            });
            const result = await response.json();
            console.log('Test update triggered:', result.message);
            return result;
        } catch (error) {
            console.error('Error triggering test update:', error);
            throw error;
        }
    }
}

// Export cho sử dụng
window.PricingClient = PricingClient;
