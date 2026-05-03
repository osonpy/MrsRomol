import { ProductCard } from './ProductCard'

export function ProductGrid({ products }) {
  return (
    <div className="grid grid-cols-2 gap-3 px-4">
      {products.map((p) => (
        <ProductCard key={p.id} product={p} />
      ))}
    </div>
  )
}
