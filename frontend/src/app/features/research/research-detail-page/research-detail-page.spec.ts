import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ResearchDetailPage } from './research-detail-page';

describe('ResearchDetailPage', () => {
  let component: ResearchDetailPage;
  let fixture: ComponentFixture<ResearchDetailPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ResearchDetailPage],
    }).compileComponents();

    fixture = TestBed.createComponent(ResearchDetailPage);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
