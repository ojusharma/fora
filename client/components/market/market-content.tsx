import { CreateListingSection } from "@/components/market/create-listing-section";

interface MarketContentProps {
  baseUrl: string;
}

async function fetchListings(baseUrl: string) {
  try {
    const res = await fetch(`${baseUrl}/api/v1/listings`, {
      cache: "no-store",
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    return [];
  }
  return [];
}

export async function MarketContent({ baseUrl }: MarketContentProps) {
  const initialListings = await fetchListings(baseUrl);

  return (
    <div className="flex-1 flex flex-col gap-20 max-w-6xl w-full p-5">
      <main className="flex-1 flex flex-col gap-6 px-0">
        <h1 className="text-2xl font-semibold">Marketplace</h1>
        <p className="text-sm text-muted-foreground">
          Create a new listing and then manage it from the &quot;My
          listings&quot; tab.
        </p>
        <CreateListingSection initialListings={initialListings} />
      </main>
    </div>
  );
}
