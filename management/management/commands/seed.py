# ruff: noqa

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from channels.models import Channel
from posts.models import Post
from comments.models import Comment
from votes.models import PostVote, CommentVote
from subscriptions.models import Subscription
from claims.models import Claim, FactCheck, FactCheckSource
from common.test_utils import disable_fact_checking_signals

USERS_DATA = [
    {"username": "john_smith", "email": "john.smith@example.com", "password": "password123", "first_name": "John", "last_name": "Smith"},
    {"username": "alice_johnson", "email": "alice.j@example.com", "password": "password123", "first_name": "Alice", "last_name": "Johnson"},
    {"username": "robert_wilson", "email": "robert.w@example.com", "password": "password123", "first_name": "Robert", "last_name": "Wilson"},
    {"username": "emily_davis", "email": "emily.d@example.com", "password": "password123", "first_name": "Emily", "last_name": "Davis"},
    {"username": "michael_brown", "email": "michael.b@example.com", "password": "password123", "first_name": "Michael", "last_name": "Brown"}
]

CHANNELS_DATA = [
    {"name": "Climate Science", "description": "Discussion about climate change research and developments", "slug": "climate-science"},
    {"name": "Health Facts", "description": "Accurate information about health, medicine, and wellness", "slug": "health-facts"},
    {"name": "Tech News", "description": "Latest developments in technology and computing", "slug": "tech-news"},
    {"name": "Politics Today", "description": "Political discourse and fact-checking", "slug": "politics-today"},
    {"name": "Economic Insights", "description": "Analysis of economic trends and financial news", "slug": "economic-insights"}
]

POSTS_DATA = [
    {"title": "New Study Shows Ocean Temperatures Rising Faster Than Expected", 
     "content": "Recent research published in Nature Climate indicates that ocean temperatures have risen 40% faster than previously estimated by the IPCC. The study analyzed data from improved measurement systems deployed over the last decade."},
    
    {"title": "Vitamin D Supplementation Benefits May Be Overstated", 
     "content": "A comprehensive meta-analysis published in the Journal of Medicine suggests that the benefits of vitamin D supplementation for healthy adults may have been overstated in previous research. The study found minimal effects on bone density and overall mortality."},
    
    {"title": "Quantum Computing Breakthrough Achieved at MIT", 
     "content": "Researchers at MIT have demonstrated a new approach to quantum computing that may solve the decoherence problem that has limited quantum computers. The technique involves novel materials that are more resistant to environmental interference."},
    
    {"title": "Analysis of Recent Economic Policy Changes", 
     "content": "The recent shift in monetary policy by central banks represents a significant departure from post-2008 approaches. This analysis examines the potential impacts on inflation, employment, and economic growth over the next five years."},
    
    {"title": "Fact-Checking Last Night's Presidential Debate", 
     "content": "During yesterday's debate, several claims were made regarding healthcare statistics. This post examines the factual basis of those claims using data from the Congressional Budget Office and Department of Health."}
]

COMMENTS_DATA = [
    {"content": "This research aligns with what NASA and NOAA have been reporting. The methodology seems particularly robust."},
    {"content": "I thought the previous IPCC estimates already accounted for these measurement improvements?"},
    {"content": "Important to note that this applies to healthy adults only, not those with diagnosed deficiencies."},
    {"content": "The study didn't address seasonal variation in vitamin D levels, which I think is a significant limitation."},
    {"content": "This could be revolutionary if it scales. Quantum computing has promised breakthroughs for decades."},
    {"content": "The article doesn't mention how they're addressing error correction, which has been the main obstacle."},
    {"content": "The analysis doesn't fully account for supply chain disruptions that are still affecting global markets."},
    {"content": "Interesting how they're predicting lower inflation than most other economic forecasts I've seen."},
    {"content": "The candidate's claim about healthcare costs was completely inaccurate according to the latest CMS data."},
    {"content": "I appreciated how you compared statements against historical voting records. Very enlightening."}
]

REPLY_DATA = [
    {"content": "That's true, but the new measurement systems have much higher precision in deeper ocean layers."},
    {"content": "You're right about the seasonal variation. That's discussed in the supplementary materials but should've been in the main paper."},
    {"content": "Error correction is briefly mentioned in the methods section - they're using a topological approach similar to Microsoft's."},
    {"content": "Good point. The analysis focuses more on monetary policy effects and less on supply-side constraints."},
    {"content": "The CMS data shows a 12% increase, not the 30% claimed during the debate. Important distinction."}
]

NESTED_REPLY_DATA = [
    {"content": "That's a good point about precision. The resolution is now down to 0.01°C in some instruments."},
    {"content": "The supplementary materials also had some interesting caveats about the statistical methodology they used."},
    {"content": "Microsoft's approach has struggled with scalability though. This new MIT approach seems to address that limitation."},
    {"content": "Supply chain issues might normalize by Q3 2025 according to most logistics analysts."},
    {"content": "The fact-checking team also found several other statistical errors in the debate that weren't mentioned in the main article."}
]

DEEP_NESTED_REPLY_DATA = [
    {"content": "Those high-precision instruments were actually developed at Woods Hole Oceanographic Institution."},
    {"content": "I wonder if the peer reviewers raised those same methodological concerns."},
    {"content": "True, the MIT paper mentions they achieved 70% better scalability in their simulations."},
    {"content": "I've seen projections ranging from Q3 2025 to Q2 2026, depending on regional factors."},
    {"content": "Did they publish the full fact-check documentation anywhere? I'd like to review the complete analysis."}
]

CLAIMS_DATA = [
    {
        "claim": {
            "extracted_claim": "Ocean temperatures have risen 40% faster than previously estimated by the IPCC.",
            "source_type": "post",
            "claim_index": 1,
            "post_id": None  
        },
        "fact_check": {
            "verdict": "not_found",
            "summary": "The claim suggests a specific rate of increase in ocean temperatures relative to previous IPCC estimates. While the available evidence confirms that \"ocean temperatures have increased\" and that the \"tropical ocean has been warming faster than other regions since 1950,\" it does not provide enough information to assess whether the current rate is 40% faster than previous IPCC estimates.",
            "sources": [
                {
                    "url": "https://en.wikipedia.org/wiki/IPCC%20Fourth%20Assessment%20Report",
                    "title": "IPCC Fourth Assessment Report",
                    "description": "Cold days, cold nights, and frost events have become less frequent. Hot days, hot nights, and heat waves have become more frequent. Additionally:\n Eleven of the twelve years in the period (1995–2006) rank among the top 12 warmest years in the instrumental record (since 1880).\n Observations since 1961 show that the ocean has been absorbing more than 80% of the heat added to the climate system, and that ocean temperatures have increased to depths of at least 3000 m (9800 ft).",
                    "relevance_score": 0.95
                },
                {
                    "url": "https://en.wikipedia.org/wiki/Sea%20surface%20temperature",
                    "title": "Sea surface temperature",
                    "description": "The tropical ocean has been warming faster than other regions since 1950, with the greatest rates of warming in the tropical Indian Ocean, western Pacific Ocean, and western boundary currents of the subtropical gyres.",
                    "relevance_score": 0.90
                }
            ]
        }
    },
    {
        "claim": {
            "extracted_claim": "The study analyzed data from improved measurement systems deployed over the last decade.",
            "source_type": "post",
            "claim_index": 2,
            "post_id": None
        },
        "fact_check": {
            "verdict": "not_found",
            "summary": "The available evidence discusses \"weather instruments\" used to study climate, technological progress in \"security alarm\" systems and changes to the \"Methods-time measurement\" data. While it mentions advancements and improvements in measurement systems, none of the evidence directly supports the claim that a study analyzed data from improved measurement systems deployed over the last decade.",
            "sources": [
                {
                    "url": "https://en.wikipedia.org/wiki/Climate",
                    "title": "Climate",
                    "description": "Details of the modern climate record are known through the taking of measurements from such weather instruments as thermometers, barometers, and anemometers during the past few centuries.",
                    "relevance_score": 0.85
                }
            ]
        }
    },
    {
        "claim": {
            "extracted_claim": "Recent research was published in Nature Climate.",
            "source_type": "post",
            "claim_index": 3,
            "post_id": None
        },
        "fact_check": {
            "verdict": "supported",
            "summary": "The available evidence supports the claim that recent research was published in Nature Climate. Drew Shindell, for example, published \"Quantified, Localized Health Benefits of Accelerated Carbon Dioxide Emissions Reductions\" in \"Nature Climate Change 8, (2018)\".",
            "sources": [
                {
                    "url": "https://en.wikipedia.org/wiki/Drew%20Shindell",
                    "title": "Drew Shindell",
                    "description": "Shindell et al: Quantified, Localized Health Benefits of Accelerated Carbon Dioxide Emissions Reductions. In: Nature Climate Change 8, (2018), 291-291, https://doi.org/10.1038/s41558-018-0108-y.",
                    "relevance_score": 0.97
                }
            ]
        }
    },
    {
        "claim": {
            "extracted_claim": "A meta-analysis was published in the Journal of Medicine.",
            "source_type": "post",
            "claim_index": 1,
            "post_id": None
        },
        "fact_check": {
            "verdict": "not_found",
            "summary": "I cannot confirm your claim that \"A meta-analysis was published in the Journal of Medicine\" based on the available evidence. While there are mentions of meta-analyses and medical journals, none of the provided text specifically confirms a meta-analysis was published in a journal *called* \"Journal of Medicine.\"",
            "sources": [
                {
                    "url": "https://en.wikipedia.org/wiki/Publication%20bias",
                    "title": "Publication bias",
                    "description": "Evidence of publication bias was found in meta-analyses published in prominent medical journals.",
                    "relevance_score": 0.88
                }
            ]
        }
    },
    {
        "claim": {
            "extracted_claim": "Researchers at MIT have demonstrated a new approach to quantum computing.",
            "source_type": "post",
            "claim_index": 1,
            "post_id": None
        },
        "fact_check": {
            "verdict": "supported",
            "summary": "The available evidence suggests that researchers at MIT are indeed involved in advancing quantum computing. As stated in the evidence, \"The Harvard research team was supported by MIT, QuEra Computing, Caltech, and Princeton University and funded by DARPA's Optimization with Noisy Intermediate-Scale Quantum devices (ONISQ) program.\"",
            "sources": [
                {
                    "url": "https://en.wikipedia.org/wiki/Quantum%20computing",
                    "title": "Quantum computing",
                    "description": "In December 2023, scientists at Harvard University successfully created \"quantum circuits\" that correct errors more efficiently than alternative methods. The Harvard research team was supported by MIT, QuEra Computing, Caltech, and Princeton University.",
                    "relevance_score": 0.96
                }
            ]
        }
    },
    {
        "claim": {
            "extracted_claim": "The approach may solve the decoherence problem that has limited quantum computers.",
            "source_type": "post",
            "claim_index": 2,
            "post_id": None
        },
        "fact_check": {
            "verdict": "supported",
            "summary": "The available evidence supports the claim that decoherence is a problem that has limited quantum computers. The evidence states that \"Decoherence represents a challenge for the practical realization of quantum computers\" because \"such machines are expected to rely heavily on the undisturbed evolution of quantum coherences.\"",
            "sources": [
                {
                    "url": "https://en.wikipedia.org/wiki/Quantum%20decoherence",
                    "title": "Quantum decoherence",
                    "description": "Decoherence represents a challenge for the practical realization of quantum computers, since such machines are expected to rely heavily on the undisturbed evolution of quantum coherences.",
                    "relevance_score": 0.99
                }
            ]
        }
    },
    {
        "claim": {
            "extracted_claim": "This applies to healthy adults only.",
            "source_type": "comment",
            "claim_index": 1,
            "comment_id": None
        },
        "fact_check": {
            "verdict": "not_found",
            "summary": "The available evidence from Wikipedia discusses age restrictions and categories such as \"Suitable only for adults aged 18 or older\" in television content ratings, services for \"adults with disabilities,\" and \"Adults Only\" resorts. However, there is no available evidence to directly support or contradict the claim.",
            "sources": [
                {
                    "url": "https://en.wikipedia.org/wiki/Television%20content%20rating%20system",
                    "title": "Television content rating system",
                    "description": "Adulto: Suitable only for adults aged 18 or older (only allowed between 11:00 p.m. and 5:00 a.m.).",
                    "relevance_score": 0.65
                }
            ]
        }
    },
    {
        "claim": {
            "extracted_claim": "Quantum technology has been stagnant for 20 years.",
            "source_type": "comment",
            "claim_index": 1,
            "comment_id": None
        },
        "fact_check": {
            "verdict": "contradicted",
            "summary": "The claim that quantum technology has been stagnant for 20 years is contradicted by the available evidence. While one excerpt notes that \"research in quantum information theory became stagnant in the 1980s\", other excerpts describe quantum computing as \"an emerging technology\" with significant advancements and investment.",
            "sources": [
                {
                    "url": "https://en.wikipedia.org/wiki/History%20of%20computing%20hardware",
                    "title": "History of computing hardware",
                    "description": "Quantum computing is an emerging technology in the field of computing. MIT Technology Review reported 10 November 2017 that IBM has created a 50-qubit computer; currently its quantum state lasts 50 microseconds.",
                    "relevance_score": 0.93
                }
            ]
        }
    },
    {
        "claim": {
            "extracted_claim": "NASA has not been to space in 30 years.",
            "source_type": "comment",
            "claim_index": 1,
            "comment_id": None
        },
        "fact_check": {
            "verdict": "contradicted",
            "summary": "The claim that NASA has not been to space in 30 years is contradicted by the available evidence. The available evidence states that the Hubble Space Telescope is \"designed to be maintained in space by astronauts.\" Furthermore, \"Five Space Shuttle missions have repaired, upgraded, and replaced systems on the telescope\". The fifth mission occurred in 2009.",
            "sources": [
                {
                    "url": "https://en.wikipedia.org/wiki/Hubble%20Space%20Telescope",
                    "title": "Hubble Space Telescope",
                    "description": "Hubble is the only telescope designed to be maintained in space by astronauts. Five Space Shuttle missions have repaired, upgraded, and replaced systems on the telescope. The fifth mission was completed in 2009.",
                    "relevance_score": 0.98
                }
            ]
        }
    },
    {
        "claim": {
            "extracted_claim": "Inflation is a myth.",
            "source_type": "comment",
            "claim_index": 1,
            "comment_id": None
        },
        "fact_check": {
            "verdict": "contradicted",
            "summary": "The claim that \"Inflation is a myth\" is contradicted by the available evidence. While one source disputes the existence of cost-push inflation, describing it as a myth, another source defines inflation as \"the decrease in the purchasing power of a currency,\" explaining how rising prices affect different sectors of the economy and erode the real value of money.",
            "sources": [
                {
                    "url": "https://en.wikipedia.org/wiki/Inflation",
                    "title": "Inflation",
                    "description": "Inflation is the decrease in the purchasing power of a currency. That is, when the general level of prices rise, each monetary unit can buy fewer goods and services in aggregate.",
                    "relevance_score": 0.99
                }
            ]
        }
    },
    {
        "claim": {
            "extracted_claim": "Vatican City has the lowest taxes in the world.",
            "source_type": "comment",
            "claim_index": 2,
            "comment_id": None
        },
        "fact_check": {
            "verdict": "supported",
            "summary": "The claim that Vatican City has the lowest taxes in the world is supported by the available evidence. The evidence states that \"Vatican City has no taxes, and items are duty-free,\" suggesting it has a tax rate lower than any other country.",
            "sources": [
                {
                    "url": "https://en.wikipedia.org/wiki/Vatican%20City",
                    "title": "Vatican City",
                    "description": "Vatican City contains religious and cultural sites such as St. Peter's Basilica, the Sistine Chapel, the Vatican Apostolic Library, and the Vatican Museums. The unique economy of Vatican City is supported financially by donations from the faithful, by the sale of postage stamps and souvenirs, fees for admission to museums, and sales of publications. Vatican City has no taxes, and items are duty-free.",
                    "relevance_score": 1.0
                }
            ]
        }
    }
]

class Command(BaseCommand):
    help = 'Seed database with predefined data'

    def add_arguments(self, parser):
        parser.add_argument('--channels', type=int, default=5, help='Number of channels to create')
        parser.add_argument('--posts', type=int, default=5, help='Number of posts per channel')
        parser.add_argument('--comments', type=int, default=10, help='Total number of comments')
        parser.add_argument('--votes', type=int, default=15, help='Number of votes per post/comment')
        parser.add_argument('--subscriptions', type=int, default=3, help='Number of subscriptions per user')

    def handle(self, *args, **options):
  
        self.stdout.write('Creating users...')
        users = []
        for user_data in USERS_DATA:
            user, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults={
                    "email": user_data["email"],
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"]
                }
            )
            if created:
                user.set_password(user_data["password"])
                user.save()
                self.stdout.write(f'Created user: {user.username}')
            users.append(user)
        
        self.stdout.write('Creating channels...')
        channels = []
        for i, channel_data in enumerate(CHANNELS_DATA):
            owner = users[i % len(users)] 
            
            channel, created = Channel.objects.get_or_create(
                name=channel_data["name"],
                defaults={
                    'description': channel_data["description"],
                    'slug': channel_data["slug"],
                    'owner': owner
                }
            )
            channels.append(channel)
            if created:
                self.stdout.write(f'Created channel: {channel.name}')
        
        self.stdout.write('Creating posts...')
        posts = []
        post_count = min(options["posts"], len(POSTS_DATA))
        
        with disable_fact_checking_signals():
            for i in range(post_count):
                post_data = POSTS_DATA[i]
                channel = channels[i % len(channels)]
                author = users[i % len(users)]
                
                post, created = Post.objects.get_or_create(
                    title=post_data["title"],
                    defaults={
                        'content': post_data["content"],
                        'author': author,
                        'channel': channel
                    }
                )
                
                posts.append(post)
                if created:
                    self.stdout.write(f'Created post: {post.title[:30]}...')
        
        self.stdout.write('Creating comments and nested replies...')
        comments = []
        comment_count = min(options["comments"], len(COMMENTS_DATA))

        with disable_fact_checking_signals():
       
            level1_comments = []
            for i in range(comment_count):
                comment_data = COMMENTS_DATA[i]
                post = posts[i % len(posts)]
                author = users[(i + 2) % len(users)] 
                
                comment, created = Comment.objects.get_or_create(
                    content=comment_data["content"],
                    post=post,
                    author=author,
                    defaults={
                        'parent_comment': None
                    }
                )
                comments.append(comment)
                level1_comments.append(comment)
            
            level2_comments = []
            for i, reply_data in enumerate(REPLY_DATA):
                parent_comment = level1_comments[i % len(level1_comments)]
                post = parent_comment.post
                author = users[(i + 3) % len(users)] 
                
                reply, created = Comment.objects.get_or_create(
                    content=reply_data["content"],
                    post=post,
                    author=author,
                    defaults={
                        'parent_comment': parent_comment
                    }
                )
                comments.append(reply)
                level2_comments.append(reply)
            
            level3_comments = []
            for i, nested_reply_data in enumerate(NESTED_REPLY_DATA):
                parent_comment = level2_comments[i % len(level2_comments)]
                post = parent_comment.post
                author = users[(i + 1) % len(users)]
                
                nested_reply, created = Comment.objects.get_or_create(
                    content=nested_reply_data["content"],
                    post=post,
                    author=author,
                    defaults={
                        'parent_comment': parent_comment
                    }
                )
                comments.append(nested_reply)
                level3_comments.append(nested_reply)
            
            for i, deep_nested_reply_data in enumerate(DEEP_NESTED_REPLY_DATA):
                parent_comment = level3_comments[i % len(level3_comments)]
                post = parent_comment.post
                author = users[(i + 4) % len(users)] 
                
                deep_nested_reply, created = Comment.objects.get_or_create(
                    content=deep_nested_reply_data["content"],
                    post=post,
                    author=author,
                    defaults={
                        'parent_comment': parent_comment
                    }
                )
                comments.append(deep_nested_reply)
        
        self.stdout.write('Creating votes...')
    
        for post in posts:
            voters = [users[i % len(users)] for i in range(len(users))]
            for i, user in enumerate(voters):
                is_upvote = i < (len(voters) * 2 // 3)
                PostVote.objects.get_or_create(
                    post=post,
                    user=user,
                    defaults={'is_upvote': is_upvote}
                )
        
        for comment in comments:
            voters = [users[i % len(users)] for i in range(len(users) - 1)]
            for i, user in enumerate(voters):
                is_upvote = i < (len(voters) * 2 // 3)
                CommentVote.objects.get_or_create(
                    comment=comment,
                    user=user,
                    defaults={'is_upvote': is_upvote}
                )
        
        self.stdout.write('Creating subscriptions...')
        for user in users:
            user_channels = [channels[i % len(channels)] for i in range(user.id, user.id + min(3, len(channels)))]
            for channel in user_channels:
                Subscription.objects.get_or_create(
                    subscriber=user,
                    channel=channel
                )
        
        self.stdout.write('Creating claims and fact checks...')
        
        self.assign_content_to_claims(posts, comments)
        
        with disable_fact_checking_signals():
            for claim_data in CLAIMS_DATA:
                claim_info = claim_data["claim"]
                fact_check_info = claim_data["fact_check"]
                
                if claim_info["source_type"] == "post":
                    post_id = claim_info["post_id"]
                    comment_id = None
                    if post_id is None or post_id >= len(posts):
                        content_object = posts[0]
                        post_id = content_object.id
                    else:
                        content_object = posts[post_id]
                else:  
                    comment_id = claim_info["comment_id"]
                    if comment_id is None or comment_id >= len(comments):
                        content_object = comments[0]
                        comment_id = content_object.id
                        post_id = content_object.post_id
                    else:
                        content_object = comments[comment_id]
                        post_id = content_object.post_id
                
                user = content_object.author
                
                try:
                    existing_claim = Claim.objects.filter(
                        extracted_claim=claim_info["extracted_claim"],
                        source_type=claim_info["source_type"],
                        user_id=user.id,
                        post_id=post_id,
                        comment_id=comment_id,
                        claim_index=claim_info["claim_index"]
                    ).first()
                    
                    if existing_claim:
                        claim = existing_claim
                        created = False
                    else:
                        claim = Claim.objects.create(
                            user_id=user.id,
                            source_type=claim_info["source_type"],
                            source_text=claim_info["extracted_claim"],
                            post_id=post_id,
                            comment_id=comment_id,
                            claim_index=claim_info["claim_index"],
                            extracted_claim=claim_info["extracted_claim"]
                        )
                        created = True
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error creating claim: {e}"))
                    continue
                
                if created:
                    self.stdout.write(f'Created claim: {claim.extracted_claim[:40]}...')
                    
                    fact_check = FactCheck.objects.create(
                        claim=claim,
                        verdict=fact_check_info["verdict"],
                        summary=fact_check_info["summary"]
                    )
                    
                    for source_data in fact_check_info["sources"]:
                        FactCheckSource.objects.create(
                            fact_check=fact_check,
                            url=source_data["url"],
                            title=source_data["title"],
                            description=source_data["description"],
                            relevance_score=source_data.get("relevance_score", 0.85)
                        )
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded database with predefined data'))
    
    def assign_content_to_claims(self, posts, comments):
        """Assign posts and comments to claims based on content matching"""
        
        post_claims = [c for c in CLAIMS_DATA if c["claim"]["source_type"] == "post"]
        comment_claims = [c for c in CLAIMS_DATA if c["claim"]["source_type"] == "comment"]
        
        for i, claim in enumerate(post_claims):
            claim["claim"]["post_id"] = i % len(posts)
        
        level1 = [c for c in comments if c.parent_comment is None]
        level2 = [c for c in comments if c.parent_comment is not None and c.parent_comment.parent_comment is None]
        level3 = [c for c in comments if c.parent_comment is not None and 
                  c.parent_comment.parent_comment is not None and
                  c.parent_comment.parent_comment.parent_comment is None]
        level4 = [c for c in comments if c.parent_comment is not None and 
                  c.parent_comment.parent_comment is not None and
                  c.parent_comment.parent_comment.parent_comment is not None]
        
        for i, claim in enumerate(comment_claims):
            level_selector = i % 4  
            
            if level_selector == 0 and level1:
                comment_index = (i // 4) % len(level1)
                claim["claim"]["comment_id"] = level1[comment_index].id
            elif level_selector == 1 and level2:
                comment_index = (i // 4) % len(level2)
                claim["claim"]["comment_id"] = level2[comment_index].id
            elif level_selector == 2 and level3:
                comment_index = (i // 4) % len(level3)
                claim["claim"]["comment_id"] = level3[comment_index].id
            elif level_selector == 3 and level4:
                comment_index = (i // 4) % len(level4)
                claim["claim"]["comment_id"] = level4[comment_index].id
            else:
  
                claim["claim"]["comment_id"] = i % len(comments)