import { router, protectedProcedure } from "./_core/trpc";
import { TRPCError } from "@trpc/server";
import { fetchAndPostNews } from "./newsService";

export const newsRouter = router({
  // Manually trigger news fetch (admin only)
  fetchNews: protectedProcedure.mutation(async ({ ctx }) => {
    if (ctx.user.role !== 'admin') {
      throw new TRPCError({ code: "FORBIDDEN", message: "Admin access required" });
    }

    const result = await fetchAndPostNews();
    return result;
  }),
});
