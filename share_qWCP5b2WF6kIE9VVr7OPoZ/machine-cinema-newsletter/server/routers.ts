import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, protectedProcedure, router } from "./_core/trpc";
import { z } from "zod";
import * as db from "./db";
import { storagePut, storageGet } from "./storage";
import { TRPCError } from "@trpc/server";
import { newsRouter } from "./newsRouter";

export const appRouter = router({
    // if you need to use socket.io, read and register route in server/_core/index.ts, all api should start with '/api/' so that the gateway can route correctly
  system: systemRouter,
  news: newsRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  newsletter: router({
    // Get all newsletters
    list: publicProcedure.query(async () => {
      return await db.getAllNewsletters();
    }),

    // Get newsletter by date
    getByDate: publicProcedure
      .input(z.object({ date: z.string() }))
      .query(async ({ input }) => {
        return await db.getNewsletterByDate(input.date);
      }),

    // Get newsletter with articles
    getWithArticles: publicProcedure
      .input(z.object({ id: z.number() }))
      .query(async ({ input }) => {
        const newsletters = await db.getAllNewsletters();
        const newsletter = newsletters.find(n => n.id === input.id);
        if (!newsletter) {
          throw new TRPCError({ code: "NOT_FOUND", message: "Newsletter not found" });
        }
        const articles = await db.getArticlesByNewsletterId(input.id);
        return { newsletter, articles };
      }),

    // Generate newsletter (admin only)
    generate: protectedProcedure
      .input(z.object({
        date: z.string().optional(),
        forceRegenerate: z.boolean().optional(),
      }))
      .mutation(async ({ input, ctx }) => {
        // Check if user is admin
        if (ctx.user.role !== 'admin') {
          throw new TRPCError({ code: "FORBIDDEN", message: "Admin access required" });
        }

        const date = input.date || new Date().toISOString().split('T')[0];

        // Check if newsletter already exists
        const existing = await db.getNewsletterByDate(date);
        if (existing && !input.forceRegenerate) {
          throw new TRPCError({ 
            code: "BAD_REQUEST", 
            message: "Newsletter for this date already exists" 
          });
        }

        // TODO: Implement actual newsletter generation logic
        // For now, create a placeholder
        const newsletter = await db.createNewsletter({
          date,
          title: `Machine Cinema - Przegląd AI (PL) – ${date}`,
          itemCount: 0,
          published: true,
        });

        return newsletter;
      }),

    // Upload newsletter files to S3
    uploadFiles: protectedProcedure
      .input(z.object({
        newsletterId: z.number(),
        htmlContent: z.string(),
        mdContent: z.string(),
      }))
      .mutation(async ({ input, ctx }) => {
        if (ctx.user.role !== 'admin') {
          throw new TRPCError({ code: "FORBIDDEN", message: "Admin access required" });
        }

        const newsletters = await db.getAllNewsletters();
        const newsletter = newsletters.find(n => n.id === input.newsletterId);
        if (!newsletter) {
          throw new TRPCError({ code: "NOT_FOUND", message: "Newsletter not found" });
        }

        // Upload HTML file
        const htmlKey = `newsletters/${newsletter.date}.html`;
        const htmlResult = await storagePut(htmlKey, input.htmlContent, "text/html");

        // Upload MD file
        const mdKey = `newsletters/${newsletter.date}.md`;
        const mdResult = await storagePut(mdKey, input.mdContent, "text/markdown");

        // Update newsletter with file URLs
        await db.updateNewsletter(input.newsletterId, {
          htmlFileKey: htmlKey,
          htmlFileUrl: htmlResult.url,
          mdFileKey: mdKey,
          mdFileUrl: mdResult.url,
        });

        return {
          htmlUrl: htmlResult.url,
          mdUrl: mdResult.url,
        };
      }),
  }),

  article: router({
    // Get latest articles
    getLatest: publicProcedure
      .input(z.object({ limit: z.number().optional().default(12) }))
      .query(async ({ input }) => {
        return await db.getLatestArticles(input.limit);
      }),

    // Get article by ID
    getById: publicProcedure
      .input(z.object({ id: z.number() }))
      .query(async ({ input }) => {
        return await db.getArticleById(input.id);
      }),

    // Get articles for a newsletter
    getByNewsletterId: publicProcedure
      .input(z.object({ newsletterId: z.number() }))
      .query(async ({ input }) => {
        return await db.getArticlesByNewsletterId(input.newsletterId);
      }),

    // Create article (admin only)
    create: protectedProcedure
      .input(z.object({
        newsletterId: z.number(),
        title: z.string(),
        summary: z.string().optional(),
        url: z.string(),
        source: z.string().optional(),
        category: z.string().optional(),
      }))
      .mutation(async ({ input, ctx }) => {
        if (ctx.user.role !== 'admin') {
          throw new TRPCError({ code: "FORBIDDEN", message: "Admin access required" });
        }

        return await db.createArticle(input);
      }),
  }),

  seenUrl: router({
    // Check if URL is seen
    check: publicProcedure
      .input(z.object({ url: z.string() }))
      .query(async ({ input }) => {
        return await db.isUrlSeen(input.url);
      }),

    // Mark URL as seen (admin only)
    mark: protectedProcedure
      .input(z.object({ url: z.string() }))
      .mutation(async ({ input, ctx }) => {
        if (ctx.user.role !== 'admin') {
          throw new TRPCError({ code: "FORBIDDEN", message: "Admin access required" });
        }

        await db.markUrlAsSeen(input.url);
        return { success: true };
      }),

    // Get all seen URLs (admin only)
    list: protectedProcedure.query(async ({ ctx }) => {
      if (ctx.user.role !== 'admin') {
        throw new TRPCError({ code: "FORBIDDEN", message: "Admin access required" });
      }

      return await db.getSeenUrls();
    }),
  }),
});

export type AppRouter = typeof appRouter;
