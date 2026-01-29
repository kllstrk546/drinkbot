def get_profiles_for_swiping_exact_city(self, user_id: int, city_normalized: str, gender_filter: str = None, who_pays_filter: str = None) -> List[Dict[str, Any]]:
    """Get profiles for swiping in exact city only with filters"""
    try:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build WHERE conditions for exact city only
            conditions = [
                "p.user_id != ?", 
                "p.city_normalized = ?",
                "p.user_id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = ?)",
                "p.user_id NOT IN (SELECT profile_id FROM profile_views WHERE user_id = ? AND view_date = DATE('now'))",
                "(p.is_bot = 0 OR (p.city_normalized = ? AND p.last_rotation_date = DATE('now')))"
            ]
            params = [user_id, city_normalized, user_id, user_id, city_normalized]
            
            # Add gender filter
            if gender_filter and gender_filter != 'all':
                conditions.append("p.gender = ?")
                params.append(gender_filter)
            
            # Add who pays filter
            if who_pays_filter and who_pays_filter != 'any':
                who_pays_mapping = {
                    'i_treat': 'i_treat',
                    'you_treat': 'someone_treats',
                    'split': 'each_self',
                    'any': None
                }
                if who_pays_filter in who_pays_mapping and who_pays_mapping[who_pays_filter]:
                    conditions.append("p.who_pays = ?")
                    params.append(who_pays_mapping[who_pays_filter])
            
            query = f'''
                SELECT p.* FROM profiles p
                JOIN daily_bot_order dbo ON p.user_id = dbo.bot_user_id
                WHERE {' AND '.join(conditions)}
                AND dbo.city_normalized = ?
                AND dbo.date = DATE('now')
                ORDER BY dbo.order_index
                LIMIT 10
            '''
            
            params.append(city_normalized)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            profiles = [dict(row) for row in results]
            
            logging.info(f"DEBUG: Found {len(profiles)} profiles for user {user_id} in exact city '{city_normalized}' with filters")
            return profiles
            
    except sqlite3.Error as e:
        logging.error(f"Error getting profiles by exact city with filters: {e}")
        return []
