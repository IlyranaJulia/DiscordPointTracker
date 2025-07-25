#!/usr/bin/env python3
"""
Bulk update all historical email submissions with server roles
"""

import asyncio
from database_postgresql import PostgreSQLPointsDatabase

# Role data extracted from the previous run
ROLE_UPDATES = [
    ('1349308361413365770', 'Verified, Staff'),
    ('257312066203942912', 'Store Manager, Convention Artist, Illustrator, Verified, Gold VIP, Platinum VIP'),
    ('247489104655155200', 'keychain7, Events/coupons, Announcement, Audience, Writer, Store Manager, Convention Artist, Illustrator, Verified, Gold VIP'),
    ('183257999194718208', 'Audience, Store Manager, Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP'),
    ('544480790835232780', 'Events/coupons, Announcement, NewArrivals/Research, Audience, Writer, Store Manager, Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP'),
    ('178121510026739712', 'Events/coupons, Announcement, NewArrivals/Research, Audience, Streamer, Store Manager, Convention Artist, Illustrator, Verified, Gold VIP'),
    ('148618488208949248', 'Events/coupons, NewArrivals/Research, Verified, Gold VIP'),
    ('716944162402074680', 'Events/coupons, français, Announcement, NewArrivals/Research, Audience, Store Manager, Convention Artist, Illustrator, Verified, Gold VIP'),
    ('312257111033774090', 'suomi, Announcement, NewArrivals/Research, Audience, Store Manager, Convention Artist, Verified, Gold VIP'),
    ('83707600847241216', 'Verified, Gold VIP'),
    ('770166850226749481', 'Announcement, Kpop Lover, Store Manager, Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP'),
    ('462209917911040000', 'Events/coupons, français, NewArrivals/Research, Store Manager, Convention Artist, Illustrator, Verified, Gold VIP'),
    ('284825543315030026', 'Events/coupons, Announcement, Verified, Gold VIP'),
    ('220276600028135425', 'español, Audience, Store Manager, Convention Artist, Illustrator, Verified, Gold VIP'),
    ('245992176612409344', 'Events/coupons, NewArrivals/Research, Audience, Store Manager, Convention Artist, Illustrator, Verified, Gold VIP'),
    ('880324247107547216', 'Events/coupons, 中文, Announcement, NewArrivals/Research, Audience, Store Manager, Convention Artist, Illustrator, Verified, Gold VIP'),
    ('277189604501618688', 'Events/coupons, Announcement, NewArrivals/Research, Audience, Store Manager, Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP'),
    ('217474250553032705', 'Announcement, NewArrivals/Research, Audience, Store Manager, Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP'),
    ('878607466408067092', 'Verified, Gold VIP'),
    ('1348990770040012820', 'Events/coupons, NewArrivals/Research, Store Manager, Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP'),
    ('1198410644093931631', 'NewArrivals/Research, Store Manager, Convention Artist, Verified, Gold VIP'),
    ('325587406105477120', 'Events/coupons, español, Announcement, NewArrivals/Research, Audience, Store Manager, Convention Artist, Illustrator, Verified, Gold VIP'),
    ('388022797756268545', 'Events/coupons, NewArrivals/Research, Audience, Store Manager, Convention Artist, Illustrator, Verified, Gold VIP'),
    ('296077389354762253', 'Audience, Store Manager, Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP'),
    ('968971171087400970', 'Verified, Gold VIP'),
    ('735518428885942312', 'Events/coupons, NewArrivals/Research, Audience, Store Manager, Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP'),
    ('231571966807506946', 'Events/coupons, NewArrivals/Research, Audience, Store Manager, Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP'),
    ('104234673600724992', 'Audience, Store Manager, Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP'),
    ('692399701202305054', 'Events/coupons, Announcement, NewArrivals/Research, Audience, Store Manager, Convention Artist, Illustrator, Verified, Gold VIP'),
    ('285880822777643008', 'Events/coupons, Announcement, NewArrivals/Research, Audience, Store Manager, Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP'),
    ('467385901555646465', 'Events/coupons, Announcement, NewArrivals/Research, Audience, Store Manager, Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP'),
    ('1108149002769281076', 'Events/coupons, NewArrivals/Research, Verified, Gold VIP'),
    ('412061783562518528', 'Events/coupons, NewArrivals/Research, Audience, Store Manager, Convention Artist, Verified, Gold VIP'),
    ('495044225994326033', 'Events/coupons, Announcement, NewArrivals/Research, Audience, Anime Fanatic, Illustrator, Verified, Gold VIP'),
    ('339077320109326347', 'Audience, Store Manager, Convention Artist, Illustrator, Verified, Gold VIP'),
    ('477354143229411350', 'Verified, Gold VIP'),
    ('683508454505185325', 'Audience, Store Manager, Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP'),
    ('692017440917553154', 'keychain7, Verified, Gold VIP'),
    ('204119976242577409', 'Store Manager, Convention Artist, Verified, Gold VIP'),
    ('221086830928330754', 'Events/coupons, Announcement, NewArrivals/Research, Illustrator, Verified, Gold VIP'),
    ('327694306833858560', 'Events/coupons, Verified, Gold VIP'),
    ('1085361717413945416', 'NewArrivals/Research, Verified, Staff'),
    ('314311953025728512', 'Audience, Store Manager, Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP'),
    ('321643606467149827', 'Store Manager, Convention Artist, Verified, Gold VIP'),
    ('272458211817422849', 'Announcement, NewArrivals/Research, Store Manager, Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP'),
    ('1003150191370719303', 'NewArrivals/Research, Verified, Gold VIP'),
    ('525090634286235669', 'Events/coupons, español, Announcement, Server Booster, NewArrivals/Research, BLCon Artist, Store Manager, Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP, Admin'),
    ('245579038100422657', 'polski, Store Manager, Convention Artist, Illustrator, Verified, Gold VIP'),
    ('403719977808429056', 'Events/coupons, Verified, Gold VIP'),
    ('178332137378938880', 'Convention Artist, Anime Fanatic, Illustrator, Verified, Gold VIP, Platinum VIP'),
    ('267060496916545537', 'Events/coupons, Announcement, NewArrivals/Research, Store Manager, Convention Artist, Illustrator, Verified, Gold VIP, Platinum VIP')
]

async def bulk_update_roles():
    """Bulk update all historical email submissions with server roles"""
    
    db = PostgreSQLPointsDatabase()
    await db.initialize()
    
    try:
        updated_count = 0
        
        for user_id, roles in ROLE_UPDATES:
            try:
                # Update database
                update_query = """
                    UPDATE email_submissions 
                    SET server_roles = $1 
                    WHERE discord_user_id = $2
                """
                
                result = await db.execute_query(update_query, (roles, user_id))
                print(f"Updated user {user_id}: {roles[:50]}...")
                updated_count += 1
                
            except Exception as e:
                print(f"Error updating user {user_id}: {e}")
                continue
        
        print(f"\n✅ Successfully updated {updated_count} email submissions with server roles!")
        
        # Verify updates
        verify_query = "SELECT discord_user_id, discord_username, server_roles FROM email_submissions WHERE server_roles IS NOT NULL AND server_roles != '' LIMIT 5"
        results = await db.execute_query(verify_query)
        
        print("\n📋 Sample updated records:")
        for user_id, username, roles in results:
            print(f"  {username}: {roles[:50]}...")
            
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(bulk_update_roles())