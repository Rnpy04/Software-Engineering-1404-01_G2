import axios, { AxiosResponse } from 'axios';
import {
    CreateTripPayload,
    UpdateTripPayload,
    UpdateTripItemPayload,
    ReplaceItemPayload,
    BulkCreateItemPayload,
    Trip,
    TripItem,
    TripDay,
    CostBreakdownResponse,
    TripHistoryResponse,
} from '@/types/trip';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true, // For JWT in cookies
});

// Add request interceptor for JWT token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

export const destinationApi = {
    suggest: (data: any) => api.post('/destinations/suggest', data),
};

export const tripApi = {
    // 1. Create New Trip
    create: (data: CreateTripPayload): Promise<AxiosResponse<Trip>> => 
        api.post('/trips/', data),

    // 2. Get Trip Timeline (Full Details)
    getById: (tripId: number): Promise<AxiosResponse<Trip>> => 
        api.get(`/trips/${tripId}/`),

    // 3. Update Trip
    update: (tripId: number, data: UpdateTripPayload): Promise<AxiosResponse<Trip>> => 
        api.patch(`/trips/${tripId}/`, data),

    // 4. Delete Trip
    delete: (tripId: number): Promise<AxiosResponse<void>> => 
        api.delete(`/trips/${tripId}/`),

    // 5. Get Trip History
    getHistory: (): Promise<AxiosResponse<TripHistoryResponse>> => 
        api.get('/trips/history/'),

    // 6. Claim Guest Trip
    claim: (tripId: number): Promise<AxiosResponse<{ message: string; trip: Trip }>> => 
        api.post(`/trips/${tripId}/claim/`),

    // 10. Get Cost Breakdown
    getCostBreakdown: (tripId: number): Promise<AxiosResponse<CostBreakdownResponse>> => 
        api.get(`/trips/${tripId}/cost_breakdown/`),

    // 11. Export Trip to PDF
    exportPDF: (tripId: number): Promise<AxiosResponse<Blob>> => 
        api.get(`/trips/${tripId}/export_pdf/`, {
            responseType: 'blob',
        }),

    // Helper function to download PDF
    downloadPDF: async (tripId: number, filename?: string): Promise<void> => {
        const response = await tripApi.exportPDF(tripId);
        const url = window.URL.createObjectURL(response.data);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename || `trip_${tripId}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    },

    // Legacy aliases for backward compatibility
    updateTrip: (tripId: number, data: UpdateTripPayload): Promise<AxiosResponse<Trip>> => 
        api.patch(`/trips/${tripId}/`, data),
};

export const tripItemApi = {
    // 7. Update Item (Change Time)
    update: (itemId: number, data: UpdateTripItemPayload): Promise<AxiosResponse<TripItem>> => 
        api.patch(`/items/${itemId}/`, data),

    // 8. Delete Item
    delete: (itemId: number): Promise<AxiosResponse<void>> => 
        api.delete(`/items/${itemId}/`),

    // 9. Replace Item
    replace: (itemId: number, data: ReplaceItemPayload): Promise<AxiosResponse<{
        message: string;
        old_item: TripItem;
        new_item: TripItem;
    }>> => 
        api.post(`/items/${itemId}/replace/`, data),
};

export const tripDayApi = {
    // 12. Create Day in Trip
    create: (tripId: number): Promise<AxiosResponse<TripDay>> => 
        api.post(`/trips/${tripId}/days/`),

    // 13. Bulk Create Items in Day
    bulkCreateItems: (dayId: number, items: BulkCreateItemPayload[]): Promise<AxiosResponse<{
        created_count: number;
        items: TripItem[];
    }>> => 
        api.post(`/days/${dayId}/items/bulk/`, items),
};

export default api;