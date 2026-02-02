#!/usr/bin/env python
"""
수신자 추가 스크립트

사용법:
    python scripts/add_recipient.py --email user@example.com --name "홍길동"
    python scripts/add_recipient.py --email user@example.com --name "홍길동" --group MEDICAL
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.config import settings
from src.database import init_db, get_session, RecipientRepository, RecipientGroup


def add_recipient(email: str, name: str, group: str = "ALL"):
    """수신자 추가"""
    init_db(settings.database_url)

    try:
        group_enum = RecipientGroup[group.upper()]
    except KeyError:
        print(f"잘못된 그룹: {group}")
        print(f"사용 가능한 그룹: {[g.name for g in RecipientGroup]}")
        return False

    with get_session() as session:
        # 중복 확인
        existing = RecipientRepository.get_by_email(session, email)
        if existing:
            print(f"이미 등록된 이메일입니다: {email}")
            return False

        # 생성
        recipient = RecipientRepository.create(session, email, name, group_enum)
        print(f"수신자 등록 완료:")
        print(f"  - ID: {recipient.id}")
        print(f"  - 이메일: {recipient.email}")
        print(f"  - 이름: {recipient.name}")
        print(f"  - 그룹: {recipient.group.value}")

    return True


def list_recipients():
    """수신자 목록 조회"""
    init_db(settings.database_url)

    with get_session() as session:
        recipients = RecipientRepository.get_all_active(session)

        if not recipients:
            print("등록된 수신자가 없습니다.")
            return

        print(f"\n등록된 수신자 ({len(recipients)}명):")
        print("-" * 60)
        for r in recipients:
            status = "활성" if r.is_active else "비활성"
            print(f"  [{r.id}] {r.email} - {r.name or '(이름없음)'} ({r.group.value}) [{status}]")
        print("-" * 60)


def main():
    parser = argparse.ArgumentParser(description="AllergyNewsLetter 수신자 관리")
    parser.add_argument("--list", action="store_true", help="수신자 목록 조회")
    parser.add_argument("--email", type=str, help="수신자 이메일")
    parser.add_argument("--name", type=str, help="수신자 이름")
    parser.add_argument("--group", type=str, default="ALL",
                        help="수신자 그룹 (PATIENT, MEDICAL, RESEARCHER, ALL)")

    args = parser.parse_args()

    if args.list:
        list_recipients()
    elif args.email:
        if not args.name:
            print("이름을 입력해주세요 (--name)")
            sys.exit(1)
        add_recipient(args.email, args.name, args.group)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
