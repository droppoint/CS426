import json

import pytest

from somemart.models import Item, Review

from tests.factories import ItemFactory, ReviewFactory


class TestViews(object):

    @pytest.fixture()
    def item(self, db):
        return ItemFactory()

    @pytest.fixture()
    def reviews(self, item):
        reviews = ReviewFactory.create_batch(size=6, item=item)
        return reviews

    def test_post_item(self, client, db):
        """/api/v1/goods/ (POST) сохраняет товар в базе."""
        url = '/api/v1/goods/'
        data = json.dumps({
            'title': 'Сыр "Российский"',
            'description': 'Очень вкусный сыр, да еще и российский.',
            'price': 100
        })
        response = client.post(url, data=data, content_type='application/json')
        assert response.status_code == 201
        document = response.json()
        # Объект был сохранен в базу
        item = Item.objects.get(pk=document['id'])
        assert item.title == 'Сыр "Российский"'
        assert item.description == 'Очень вкусный сыр, да еще и российский.'
        assert item.price == 100

    def test_post_item_not_json(self, client):
        """/api/v1/goods/ (POST) возвращает 400 если документ не в формате
        JSON.
        """
        url = '/api/v1/goods/'
        data = {
            'title': 'Сыр "Российский"',
            'description': 'Очень вкусный сыр, да еще и российский.',
            'price': '100.15'
        }
        response = client.post(url, data=data, content_type='application/json')
        assert response.status_code == 400

    @pytest.mark.parametrize('field, value', [
        ('title', ''),
        ('title', 'A' * 65),
        ('title', 123),
        ('description', ''),
        ('description', 'Б' * 1025),
        ('description', 456),
        ('price', 'nine'),
        ('price', 1000001),
    ])
    def test_post_item_invalid(self, client, db, field, value):
        """/api/v1/goods/ (POST) возвращает 400, если документ не проходит
        валидацию.
        """
        url = '/api/v1/goods/'
        data = {
            'title': 'Сыр "Российский"',
            'description': 'Очень вкусный сыр, да еще и российский.',
            'price': 100
        }
        data[field] = value
        data = json.dumps(data)
        response = client.post(url, data=data, content_type='application/json')
        assert response.status_code == 400

    @pytest.mark.parametrize('field', [
        'title', 'description', 'price'
    ])
    def test_post_item_required_field(self, client, db, field):
        """/api/v1/goods/ (POST) возвращает 400, если документ не содержит
        всех необходимых полей.
        """
        url = '/api/v1/goods/'
        data = {
            'title': 'Сыр "Российский"',
            'description': 'Очень вкусный сыр, да еще и российский.',
            'price': 100
        }
        del(data[field])
        data = json.dumps(data)
        response = client.post(url, data=data, content_type='application/json')
        assert response.status_code == 400

    def test_post_review(self, client, item):
        """/api/v1/goods/:id/reviews/ (POST) сохраняет обзор для товара."""
        url = '/api/v1/goods/{}/reviews/'.format(item.pk)
        data = json.dumps({
            'grade': 10,
            'text': 'Самый. Лучший. Сыр.'
        })
        response = client.post(url, data=data, content_type='application/json')
        assert response.status_code == 201
        document = response.json()
        # Объект был сохранен в базу
        review = Review.objects.get(pk=document['id'])
        assert review.grade == 10
        assert review.text == 'Самый. Лучший. Сыр.'
        assert review.item == item

    def test_post_review_no_item(self, client, db):
        """/api/v1/goods/:id/reviews/ (POST) возвращает 404, если товара не
        существует.
        """
        url = '/api/v1/goods/{}/reviews/'.format(999)
        data = json.dumps({
            'grade': 10,
            'text': 'Самый. Лучший. Сыр.'
        })
        response = client.post(url, data=data, content_type='application/json')
        assert response.status_code == 404

    def test_post_review_not_json(self, client, item):
        """/api/v1/goods/:id/reviews/ (POST) возвращает 400, если документ не
        в формате JSON."""
        url = '/api/v1/goods/{}/reviews/'.format(item.pk)
        data = {
            'grade': 10,
            'text': 'Самый. Лучший. Сыр.'
        }
        response = client.post(url, data=data)
        assert response.status_code == 400

    @pytest.mark.parametrize('field, value', [
        ('grade', None),
        ('grade', 11),
        ('grade', -1),
        ('text', ''),
        ('text', 'Б' * 1025),
        ('text', 456),
    ])
    def test_post_review_invalid(self, client, field, value, item):
        """/api/v1/goods/:id/reviews/ (POST) возвращает 400, если документ не
        проходит валидацию.
        """
        url = '/api/v1/goods/{}/reviews/'.format(item.pk)
        data = {
            'grade': 10,
            'text': 'Самый. Лучший. Сыр.'
        }
        data[field] = value
        data = json.dumps(data)
        response = client.post(url, data=data, content_type='application/json')
        assert response.status_code == 400

    def test_get_item(self, client, item, reviews):
        """/api/v1/goods/:id (GET) возвращает товар с последними 5-ю
        описаниями.
        """
        url = '/api/v1/goods/{}/'.format(item.pk)
        response = client.get(url)
        assert response.status_code == 200
        document = response.json()
        assert document['id'] == item.pk
        assert document['title'] == item.title
        assert document['description'] == item.description
        assert document['price'] == item.price
        last_id = 999
        for review_dict in document['reviews']:
            assert review_dict['id'] < last_id
            last_id = review_dict['id']
            review = Review.objects.get(pk=review_dict['id'])
            assert review.grade == review_dict['grade']
            assert review.text == review_dict['text']

    def test_get_item_no_reviews(self, client, item):
        """/api/v1/goods/:id (GET) возвращает товар без отзывов."""
        url = '/api/v1/goods/{}/'.format(item.pk)
        response = client.get(url)
        assert response.status_code == 200
        document = response.json()
        assert document['id'] == item.pk
        assert document['title'] == item.title
        assert document['description'] == item.description
        assert document['price'] == item.price
        assert document['reviews'] == []

    def test_get_item_no_item(self, client, db):
        """/api/v1/goods/:id (GET) возвращает 404, если товара не существует.
        """
        url = '/api/v1/goods/999/'
        response = client.get(url)
        assert response.status_code == 404
