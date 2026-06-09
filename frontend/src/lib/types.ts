export interface Category {
  id: number;
  name: string;
  slug: string;
}

export interface Supplier {
  id: number;
  name: string;
  description: string | null;
  website: string | null;
  email: string | null;
  phone: string | null;
  city: string | null;
  region: string | null;
  delivery_regions: string[] | null;
  category: Category | null;
  min_order_amount: number | null;
  min_order_unit: string | null;
  price_range_description: string | null;
  has_certificates: boolean;
  certificate_types: string[] | null;
  delivery_conditions: string | null;
  source_url: string | null;
  source_platform: string | null;
  notes: string | null;
  inn: string | null;
  legal_name: string | null;
  verified: boolean;
  rating: number | null;
  payment_terms: string | null;
  works_with_nds: boolean | null;
  is_stale: boolean;
}

export interface SupplierSearchResult {
  supplier: Supplier;
  score: number;
  match_reason: string | null;
}

export interface SearchResponse {
  results: SupplierSearchResult[];
  ai_recommendation: string | null;
  total: number;
  query: string;
}

export interface SearchParams {
  query: string;
  category?: string;
  region?: string;
  max_min_order?: number;
  has_certificates?: boolean;
  use_ai?: boolean;
  limit?: number;
}
